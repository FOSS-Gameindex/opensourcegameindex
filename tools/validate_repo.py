#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import urlparse


GAME_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
RUNTIMES = {"", "wine", "proton", "proton-ge", "native", "auto", "windows"}
ARCHIVE_FORMATS = {"eti", "rar", "tar.gz"}


def load_json(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return raw


def valid_url(raw: str) -> bool:
    parsed = urlparse(raw)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def valid_relative_path(raw: object) -> bool:
    value = str(raw or "").strip()
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    return bool(
        value
        and "\x00" not in value
        and "\\" not in value
        and not posix.is_absolute()
        and posix.as_posix() != "."
        and not windows.is_absolute()
        and not windows.drive
        and ".." not in posix.parts
    )


def _has_configured_value(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            _has_configured_value(item)
            for key, item in value.items()
            if key != "schema_version"
        )
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None


def validate_llng_distribution(metadata: dict, metadata_path: Path) -> list[str]:
    errors: list[str] = []
    provider = str(metadata.get("game_provider_type", "")).strip().lower()
    if provider not in {"", "ouisync", "resilio", "local"}:
        errors.append(f"{metadata_path}: unsupported game_provider_type {provider!r}")
    runner = str(metadata.get("runner", "")).strip().lower()
    if runner not in RUNTIMES:
        errors.append(f"{metadata_path}: unsupported runner {runner!r}")
    tasks = metadata.get("installer_tasks", [])
    if not isinstance(tasks, list) or any(not isinstance(task, dict) for task in tasks):
        errors.append(f"{metadata_path}: installer_tasks must be a list of objects")
    size_gb = metadata.get("size_gb")
    if size_gb is not None and (
        isinstance(size_gb, bool)
        or not isinstance(size_gb, (int, float))
        or size_gb < 0
    ):
        errors.append(f"{metadata_path}: size_gb must be a non-negative number or null")
    if metadata.get("master_required") is not None and not isinstance(
        metadata.get("master_required"), bool
    ):
        errors.append(f"{metadata_path}: master_required must be a boolean or null")
    description = metadata.get("description")
    if isinstance(description, dict):
        if any(not isinstance(description.get(locale, ""), str) for locale in ("de", "en", "fr")):
            errors.append(f"{metadata_path}: localized description values must be strings")
    elif description is not None and not isinstance(description, str):
        errors.append(f"{metadata_path}: description must be a string or locale object")
    game_start = metadata.get("game_start")
    if game_start is not None:
        if not isinstance(game_start, dict):
            errors.append(f"{metadata_path}: game_start must be an object")
        else:
            start_file = game_start.get("file", "")
            if start_file and not valid_relative_path(start_file):
                errors.append(f"{metadata_path}: game_start.file must be a safe relative path")
            args = game_start.get("args", [])
            if not (
                isinstance(args, str)
                or isinstance(args, list)
                and all(isinstance(arg, str) for arg in args)
            ):
                errors.append(f"{metadata_path}: game_start.args must be a string or list of strings")

    archive_distribution = metadata.get("distribution")
    if archive_distribution is not None and _has_configured_value(archive_distribution):
        if not isinstance(archive_distribution, dict) or archive_distribution.get("schema_version") != 1:
            errors.append(f"{metadata_path}: distribution.schema_version must be 1")
        else:
            archive = archive_distribution.get("archive", {})
            if not isinstance(archive, dict):
                errors.append(f"{metadata_path}: distribution.archive must be an object")
            else:
                if not valid_relative_path(archive.get("file")):
                    errors.append(f"{metadata_path}: distribution.archive.file must be a safe relative path")
                if str(archive.get("format", "")).strip().lower() not in ARCHIVE_FORMATS:
                    errors.append(f"{metadata_path}: unsupported distribution.archive.format")
                if not SHA256_RE.fullmatch(str(archive.get("sha256", "")).strip()):
                    errors.append(f"{metadata_path}: distribution.archive.sha256 must be a SHA-256 checksum")
                if not valid_relative_path(archive.get("version_file")):
                    errors.append(f"{metadata_path}: distribution.archive.version_file must be a safe relative path")

    llng = metadata.get("llng")
    if provider == "ouisync" or (llng is not None and _has_configured_value(llng)):
        if provider != "ouisync":
            errors.append(f"{metadata_path}: LLNG distribution metadata requires game_provider_type 'ouisync'")
        if not str(metadata.get("version", "")).strip():
            errors.append(f"{metadata_path}: Ouisync games require a non-empty version")
        if archive_distribution is None:
            errors.append(f"{metadata_path}: Ouisync games require distribution.archive metadata")
        if not isinstance(llng, dict) or llng.get("schema_version") != 1:
            errors.append(f"{metadata_path}: Ouisync games require llng.schema_version 1")
            return errors
        capability = llng.get("distribution")
        if not isinstance(capability, dict):
            errors.append(f"{metadata_path}: llng.distribution must be an object")
            return errors
        if capability.get("provider") != "ouisync":
            errors.append(f"{metadata_path}: llng.distribution.provider must be ouisync")
        token = capability.get("read_token")
        if not isinstance(token, str) or not token.strip() or token != token.strip() or any(char.isspace() for char in token):
            errors.append(f"{metadata_path}: llng.distribution.read_token must be a non-empty token without whitespace")
        info_hash = capability.get("info_hash")
        if not isinstance(info_hash, str) or not info_hash.strip() or any(char.isspace() for char in info_hash):
            errors.append(f"{metadata_path}: llng.distribution.info_hash must be non-empty and contain no whitespace")
        editable = capability.get("editable_files")
        if not isinstance(editable, list) or len(editable) > 4096:
            errors.append(f"{metadata_path}: llng.distribution.editable_files must be a list with at most 4096 paths")
        elif any(not valid_relative_path(path) for path in editable) or len({str(path).casefold() for path in editable}) != len(editable):
            errors.append(f"{metadata_path}: editable_files must contain unique safe relative paths")
    return errors


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

    category = str(metadata.get("category", "")).strip()
    if not category:
        errors.append(f"{metadata_path}: missing category")
    errors.extend(validate_llng_distribution(metadata, metadata_path))

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
    try:
        source_config = load_json(root / "source.json")
    except (OSError, ValueError) as exc:
        errors.append(f"{root / 'source.json'}: {exc}")
        source_config = {}
    revision = source_config.get("index_revision", 1)
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        errors.append(f"{root / 'source.json'}: index_revision must be a positive integer")
    games_root = root / "games"
    for game_dir in sorted(p for p in games_root.iterdir() if p.is_dir()):
        errors.extend(validate_game(game_dir))
    for line in errors:
        print(line, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
