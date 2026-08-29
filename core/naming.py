from __future__ import annotations
import hashlib
import hmac
import re
from pathlib import Path
from .keys import Keys


def split_v2_plain_name(enc_path: Path) -> str:
    name = enc_path.name
    if not name.lower().endswith(".enc"):
        return name
    p = Path(name[:-4])
    match = re.match(r"^(.*)_([A-F0-9]{64})$", p.stem, re.IGNORECASE)
    return (match.group(1) if match else p.stem) + p.suffix


def default_decrypted_name(path: Path, version: str) -> str:
    if version == "v2":
        return split_v2_plain_name(path)
    return path.name[:-4] if path.name.lower().endswith(".enc") else path.name + ".dec"


def v2_hash_for_plain_filename(path_or_name: Path | str, keys: Keys) -> str:
    stem = Path(Path(path_or_name).name).stem
    return hmac.new(keys.require_hmac(), stem.encode("utf-8"), hashlib.sha256).hexdigest().upper()


def default_encrypted_name(path: Path, version: str, keys: Keys) -> str:
    if version == "v1":
        return path.name + ".enc"
    return f"{path.stem}_{v2_hash_for_plain_filename(path.name, keys)}{path.suffix}.enc"
