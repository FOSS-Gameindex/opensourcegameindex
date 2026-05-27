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


def build_index(root: Path) -> dict:
    games = []
    for game_dir in sorted(p for p in (root / "games").iterdir() if p.is_dir()):
        metadata = load_json(game_dir / "metadata.json")
        links = metadata.get("links", [])
        lan_supported = metadata.get("lan_supported")
        player_count = parse_player_count(metadata.get("max_players"))
        runtime_support = normalize_runtime_support(
            metadata.get("runtime_support", metadata.get("supported_runtimes"))
        )
        games.append(
            {
                "game_id": metadata.get("game_id", game_dir.name),
                "title": metadata.get("title", ""),
                "description": metadata.get("description", ""),
                "publisher": metadata.get("publisher", ""),
                "release_year": metadata.get("release_year", ""),
                "genre": metadata.get("genre", ""),
                "lan_supported": lan_supported,
                "max_players": metadata.get("max_players", ""),
                "player_count": player_count,
                "player_bucket": player_bucket(player_count),
                "runtime_support": runtime_support,
                "runtime_bucket": runtime_bucket(runtime_support),
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
    .badge-row {{ display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.6rem 0 0.4rem; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.3rem 0.6rem; border-radius: 999px; font-size: 0.82rem; border: 1px solid transparent; }}
    .badge-lan {{ background: rgba(68, 173, 92, 0.16); color: #9af0aa; border-color: rgba(68, 173, 92, 0.35); }}
    .badge-no-lan {{ background: rgba(255, 255, 255, 0.06); color: #c4cedb; border-color: rgba(255, 255, 255, 0.1); }}
    .filter-bar {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.75rem 0 1rem; }}
    .filter-section {{ margin: 0.75rem 0 1rem; }}
    .filter-label {{ display: block; margin: 0 0 0.35rem; color: #a8b5c6; font-size: 0.9rem; }}
    .filter-btn {{ appearance: none; border: 1px solid rgba(255,255,255,0.12); background: rgba(255,255,255,0.05); color: #e7edf5; border-radius: 999px; padding: 0.45rem 0.8rem; cursor: pointer; }}
    .filter-btn[aria-pressed="true"] {{ background: rgba(143, 211, 255, 0.16); border-color: rgba(143, 211, 255, 0.36); }}
    .cards-empty {{ color: #a8b5c6; padding: 1rem 0.25rem; }}
    .card.is-hidden {{ display: none; }}
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
    lan_count = sum(1 for entry in index["games"] if entry.get("lan_supported") is True)
    game_count = len(index["games"])
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
        image_html = ""
        if image_rel:
            image_html = (
                f'<img class="game-hero" src="{html.escape(image_rel, quote=True)}" '
                f'alt="{html.escape(title)}">'
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
        page = render_page(
            title,
            f"""
<header>
  <p class="muted"><a href="../..">Back to index</a></p>
  <h1>{html.escape(title)}</h1>
  <p class="muted">{html.escape(description)}</p>
  <div class="badge-row">
    {lan_badge}
  </div>
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
<article class="card" data-lan-supported="{1 if lan_supported else 0}" data-player-bucket="{html.escape(player_bucket_value)}" data-runtime-bucket="{html.escape(runtime_bucket_value)}">
  <h2><a href="games/{html.escape(game_id)}/index.html">{html.escape(title)}</a></h2>
  <p class="muted">{html.escape(description)}</p>
  <div class="badge-row">
    <span class="badge {'badge-lan' if lan_supported else 'badge-no-lan'}">
      {'LAN supported' if lan_supported else 'No LAN mode'}
      {f' · {html.escape(max_players)} players' if lan_supported and max_players else ''}
    </span>
  </div>
  <p><a href="games/{html.escape(game_id)}/index.html">Open game page</a></p>
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
  <div class="filter-section">
    <span class="filter-label">Catalog filter</span>
    <div class="filter-bar" role="toolbar" aria-label="Game filters">
      <button class="filter-btn" type="button" data-lan-filter="all" aria-pressed="true">All games</button>
      <button class="filter-btn" type="button" data-lan-filter="lan" aria-pressed="false">LAN supported</button>
      <button class="filter-btn" type="button" data-lan-filter="nonlan" aria-pressed="false">No LAN mode</button>
    </div>
  </div>
  <div class="filter-section">
    <span class="filter-label">Player count</span>
    <div class="filter-bar" role="toolbar" aria-label="Player count filters">
      <button class="filter-btn" type="button" data-player-filter="all" aria-pressed="true">Any count</button>
      <button class="filter-btn" type="button" data-player-filter="1-2" aria-pressed="false">1-2</button>
      <button class="filter-btn" type="button" data-player-filter="3-4" aria-pressed="false">3-4</button>
      <button class="filter-btn" type="button" data-player-filter="5-8" aria-pressed="false">5-8</button>
      <button class="filter-btn" type="button" data-player-filter="9+" aria-pressed="false">9+</button>
      <button class="filter-btn" type="button" data-player-filter="unknown" aria-pressed="false">Unknown</button>
    </div>
  </div>
  <div class="filter-section">
    <span class="filter-label">Runtime support</span>
    <div class="filter-bar" role="toolbar" aria-label="Runtime support filters">
      <button class="filter-btn" type="button" data-runtime-filter="all" aria-pressed="true">Any runtime</button>
      <button class="filter-btn" type="button" data-runtime-filter="native" aria-pressed="false">Native</button>
      <button class="filter-btn" type="button" data-runtime-filter="wine" aria-pressed="false">Wine</button>
      <button class="filter-btn" type="button" data-runtime-filter="proton" aria-pressed="false">Proton</button>
      <button class="filter-btn" type="button" data-runtime-filter="proton-ge" aria-pressed="false">Proton-GE</button>
      <button class="filter-btn" type="button" data-runtime-filter="mixed" aria-pressed="false">Mixed</button>
      <button class="filter-btn" type="button" data-runtime-filter="unknown" aria-pressed="false">Unknown</button>
    </div>
  </div>
  <section class="grid" id="games-grid">
    {''.join(games_html)}
  </section>
  <p class="cards-empty" id="games-empty" hidden>No games match the selected filter.</p>
  <script>
  (function () {{
    const buttons = Array.from(document.querySelectorAll('.filter-btn'));
    const cards = Array.from(document.querySelectorAll('#games-grid .card'));
    const empty = document.getElementById('games-empty');
    const state = {{
      lan: 'all',
      players: 'all',
      runtime: 'all',
    }};

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

    function applyFilters() {{
      let visible = 0;
      for (const card of cards) {{
        const show =
          matchesLanFilter(card, state.lan) &&
          matchesPlayerFilter(card, state.players) &&
          matchesRuntimeFilter(card, state.runtime);
        card.classList.toggle('is-hidden', !show);
        if (show) {{
          visible += 1;
        }}
      }}
      if (empty) {{
        empty.hidden = visible !== 0;
      }}
      for (const button of buttons) {{
        const active =
          (button.dataset.lanFilter && button.dataset.lanFilter === state.lan) ||
          (button.dataset.playerFilter && button.dataset.playerFilter === state.players) ||
          (button.dataset.runtimeFilter && button.dataset.runtimeFilter === state.runtime);
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      }}
    }}

    for (const button of buttons) {{
      button.addEventListener('click', () => {{
        if (button.dataset.lanFilter) {{
          state.lan = button.dataset.lanFilter || 'all';
        }}
        if (button.dataset.playerFilter) {{
          state.players = button.dataset.playerFilter || 'all';
        }}
        if (button.dataset.runtimeFilter) {{
          state.runtime = button.dataset.runtimeFilter || 'all';
        }}
        applyFilters();
      }});
    }}
    applyFilters();
  }})();
  </script>
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
