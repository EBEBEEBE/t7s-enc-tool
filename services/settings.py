from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QStandardPaths


@dataclass
class AppSettings:
    default_folder: str | None = None
    auto_export: bool = False
    temp_folder: str | None = None
    schema_version: int = 1


class SettingsService:
    def __init__(self, program_dir: Path | None = None, user_dir: Path | None = None):
        self.program_dir = (program_dir or Path(sys.argv[0]).resolve().parent).resolve()
        default_user = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
        self.user_dir = (user_dir or Path(default_user)).resolve()
        self.program_path = self.program_dir / "settings.json"
        self.user_path = self.user_dir / "settings.json"
        self.active_location = "program" if self.program_path.is_file() else "user"
        self.settings = AppSettings()
        self.load()

    @property
    def active_dir(self) -> Path:
        return self.program_dir if self.active_location == "program" else self.user_dir

    @property
    def active_path(self) -> Path:
        return self.active_dir / "settings.json"

    def load(self) -> AppSettings:
        path = self.active_path
        if not path.is_file():
            self.settings = AppSettings()
            return self.settings
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            output = raw.get("output", {})
            advanced = raw.get("advanced", {})
            self.settings = AppSettings(
                default_folder=output.get("default_folder"),
                auto_export=bool(output.get("auto_export", False)),
                temp_folder=advanced.get("temp_folder"),
                schema_version=int(raw.get("schema_version", 1)),
            )
        except (OSError, ValueError, TypeError, AttributeError):
            self.settings = AppSettings()
        return self.settings

    def save(self, settings: AppSettings | None = None) -> None:
        if settings is not None:
            self.settings = settings
        self.active_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "output": {
                "default_folder": self.settings.default_folder,
                "auto_export": self.settings.auto_export,
            },
            "advanced": {"temp_folder": self.settings.temp_folder},
        }
        temporary = self.active_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, self.active_path)

    def is_writable(self, directory: Path | None = None) -> bool:
        path = (directory or self.program_dir)
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".t7s-write-test"
            probe.write_text("", encoding="utf-8")
            probe.unlink()
            return True
        except OSError:
            return False

    def switch_location(self, location: str, keys_text: str | None = None) -> None:
        if location not in {"user", "program"}:
            raise ValueError(f"Unknown settings location: {location}")
        destination = self.program_dir if location == "program" else self.user_dir
        if not self.is_writable(destination):
            raise OSError("The selected settings folder is not writable.")
        old_location = self.active_location
        self.active_location = location
        try:
            self.save()
            if keys_text is not None:
                (destination / "keys.txt").write_text(keys_text, encoding="utf-8")
            if old_location == "program" and location == "user" and self.program_path.exists():
                self.program_path.unlink()
        except Exception:
            self.active_location = old_location
            raise

    def default_export_directory(self) -> Path | None:
        return Path(self.settings.default_folder) if self.settings.default_folder else None
