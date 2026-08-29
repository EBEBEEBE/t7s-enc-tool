from __future__ import annotations

import tempfile
from pathlib import Path


class TempFileService:
    def create_session(self, configured_folder: str | None = None) -> Path:
        base = Path(configured_folder) if configured_folder else None
        if base:
            base.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix="t7s-assetcrypt-", dir=str(base) if base else None))
