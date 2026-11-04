from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.build_site import build_index, build_site
from tools.validate_repo import validate_game


class IndexGenerationTests(unittest.TestCase):
    def _write_game(self, root: Path, *, valid: bool = True) -> Path:
        game_dir = root / "games" / "demo"
        game_dir.mkdir(parents=True)
        (game_dir / "README.md").write_text("# Demo\n", encoding="utf-8")
        metadata = {
            "game_id": "demo",
            "title": "Demo",
            "description": {
                "de": "Demo-Beschreibung.",
                "en": "Demo description.",
                "fr": "Description de démo.",
            },
            "size_gb": 2.5,
            "master_required": False,
            "game_start": {"file": "game_start.sh", "args": ["--windowed"]},
            "category": "Strategy",
            "game_provider_type": "ouisync",
            "version": "1.2.3",
            "runner": "proton",
            "installer_tasks": [{"name": "protontricks", "args": "vcrun2019"}],
            "distribution": {
                "schema_version": 1,
                "archive": {
                    "file": "demo.tar.gz",
                    "format": "tar.gz",
                    "sha256": "a" * 64,
                    "version_file": "version.ini",
                },
            },
            "llng": {
                "schema_version": 1,
                "distribution": {
                    "provider": "ouisync",
                    "read_token": "read-only-token",
                    "info_hash": "ouisync-repository-hash",
                    "editable_files": ["game_start.sh"],
                },
            },
        }
        if not valid:
            metadata["llng"]["distribution"].pop("info_hash")
        (game_dir / "metadata.json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )
        (root / "source.json").write_text(
            json.dumps({"index_revision": 7}), encoding="utf-8"
        )
        return game_dir

    def test_build_index_carries_llng_distribution_runtime_and_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._write_game(root)

            index = build_index(root)
            entry = index["games"][0]

            self.assertEqual(index["schema_version"], 2)
            self.assertEqual(index["index_revision"], 7)
            self.assertEqual(entry["version"], "1.2.3")
            self.assertEqual(entry["description"]["fr"], "Description de démo.")
            self.assertEqual(entry["size_gb"], 2.5)
            self.assertFalse(entry["master_required"])
            self.assertEqual(entry["game_start"]["file"], "game_start.sh")
            self.assertEqual(entry["runner"], "proton")
            self.assertEqual(entry["installer_tasks"][0]["name"], "protontricks")
            self.assertEqual(entry["distribution"]["archive"]["sha256"], "a" * 64)
            self.assertEqual(entry["llng"]["distribution"]["info_hash"], "ouisync-repository-hash")

            build_site(root, root / "site")
            generated = json.loads((root / "site" / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(generated["games"][0]["llng"], entry["llng"])

    def test_validator_rejects_incomplete_ouisync_publication_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game_dir = self._write_game(Path(temp), valid=False)

            errors = validate_game(game_dir)

            self.assertTrue(any("info_hash" in error for error in errors))

    def test_empty_llng_templates_are_valid_and_omitted_from_generated_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game_dir = self._write_game(root)
            metadata = json.loads((game_dir / "metadata.json").read_text(encoding="utf-8"))
            metadata.update(
                {
                    "version": "",
                    "game_provider_type": "",
                    "runner": "",
                    "installer_tasks": [],
                    "distribution": {
                        "schema_version": 1,
                        "archive": {
                            "file": "",
                            "format": "",
                            "sha256": "",
                            "version_file": "",
                        },
                    },
                    "llng": {
                        "schema_version": 1,
                        "distribution": {
                            "provider": "",
                            "read_token": "",
                            "info_hash": "",
                            "editable_files": [],
                        },
                    },
                }
            )
            (game_dir / "metadata.json").write_text(
                json.dumps(metadata), encoding="utf-8"
            )

            self.assertEqual(validate_game(game_dir), [])
            entry = build_index(root)["games"][0]

            self.assertNotIn("distribution", entry)
            self.assertNotIn("llng", entry)


if __name__ == "__main__":
    unittest.main()
