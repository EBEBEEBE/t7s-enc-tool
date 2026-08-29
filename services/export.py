from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path

from core.detection import IMAGE_EXTENSIONS, logical_extension
from core.naming import split_v2_plain_name


class ExportService:
    @staticmethod
    def subfolder(source: Path, action: str, resolved_mode: str) -> str:
        decrypting = action == "decrypt"
        extension = logical_extension(source, decrypting)
        if extension in IMAGE_EXTENSIONS:
            if decrypting and source.name.lower().endswith(".enc"):
                name = split_v2_plain_name(source) if resolved_mode == "v2" else source.name[:-4]
            else:
                name = source.name
            prefix = re.split(r"\d", Path(name).stem, maxsplit=1)[0].rstrip("_- .")
            return prefix or "images"
        return extension.lstrip(".") or "other"

    @classmethod
    def export_file(cls, source: Path, output: Path, result, target: Path) -> Path:
        folder = target / ("Decrypted" if result.action == "decrypt" else "Encrypted") / cls.subfolder(source, result.action, result.resolved_mode)
        folder.mkdir(parents=True, exist_ok=True)
        final = folder / output.name
        with tempfile.NamedTemporaryFile(prefix=f".{final.name}.", dir=folder, delete=False) as handle:
            temporary = Path(handle.name)
        try:
            shutil.copyfile(output, temporary)
            os.replace(temporary, final)
        finally:
            temporary.unlink(missing_ok=True)
        return final
