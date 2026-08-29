from __future__ import annotations
import re
from pathlib import Path
from .errors import AssetCryptError

V2_HASH_RE = re.compile(r"_[A-F0-9]{64}(?=\.[^.]+\.enc$)", re.IGNORECASE)
ANY_64_HEX_RE = re.compile(r"[A-F0-9]{64}", re.IGNORECASE)
SOURCE_LZ4_EXTENSIONS = {".txt", ".json", ".atlas", ".sql"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".ktx", ".ktx2", ".dds", ".tga"}


def is_v2_filename(path: Path) -> bool:
    return path.name.lower().endswith(".enc") and bool(ANY_64_HEX_RE.search(path.name))


def detect_version_from_filename(path: Path) -> str:
    return "v2" if is_v2_filename(path) else "v1"


def logical_extension(path: Path, decrypting: bool) -> str:
    name = path.name[:-4] if decrypting and path.name.lower().endswith(".enc") else path.name
    return Path(name).suffix.lower()


def auto_lz4_for_path(path: Path, decrypting: bool) -> bool:
    ext = logical_extension(path, decrypting)
    if ext in SOURCE_LZ4_EXTENSIONS:
        return True
    if ext in IMAGE_EXTENSIONS:
        return False
    return True


def explicit_type(type_name: str | None) -> tuple[str, bool] | None:
    if type_name is None:
        return None
    if type_name == "v1": return "v1", False
    if type_name == "v2": return "v2", False
    if type_name == "v2z": return "v2", True
    raise AssetCryptError(f"Unknown type: {type_name}")


def choose_mode(path: Path, command: str, type_name: str | None) -> tuple[str, bool]:
    forced = explicit_type(type_name)
    if forced:
        return forced
    if command == "decrypt":
        return detect_version_from_filename(path), auto_lz4_for_path(path, True)
    return "v2", auto_lz4_for_path(path, False)
