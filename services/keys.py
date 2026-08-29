from __future__ import annotations

from pathlib import Path

from core import AssetCryptError, Keys


KEY_FIELDS = ("v1_aes_key", "v2_raw_key", "v2_signature", "hmac_key")
KEY_LABELS = {
    "v1_aes_key": "V1AESKey",
    "v2_raw_key": "V2Key",
    "v2_signature": "V2Signature",
    "hmac_key": "HMACKey",
}


class KeyService:
    def __init__(self, settings_service):
        self.settings_service = settings_service

    def load_active(self) -> Keys:
        candidates = (
            self.settings_service.active_dir / "keys.txt",
            self.settings_service.active_dir / "key.txt",
            self.settings_service.program_dir / "keys.txt",
            self.settings_service.program_dir / "key.txt",
        )
        for path in candidates:
            if path.is_file():
                return Keys.from_file(path)
        return Keys()

    @staticmethod
    def validate(keys: Keys) -> None:
        if keys.v1_aes_key is not None: keys.require_v1()
        if keys.v2_raw_key is not None: keys.require_v2_key()
        if keys.v2_signature is not None: keys.require_signature()
        if keys.hmac_key is not None: keys.require_hmac()

    @staticmethod
    def from_text(path: Path) -> Keys:
        keys = Keys.from_file(path)
        KeyService.validate(keys)
        return keys

    @staticmethod
    def to_text(keys: Keys) -> str:
        return "".join(
            f"{KEY_LABELS[field]} = {(getattr(keys, field) or b'').decode('utf-8')}\n"
            for field in KEY_FIELDS
        )

    def save(self, keys: Keys) -> None:
        self.validate(keys)
        destination = self.settings_service.active_dir
        destination.mkdir(parents=True, exist_ok=True)
        temporary = destination / "keys.txt.tmp"
        temporary.write_text(self.to_text(keys), encoding="utf-8")
        temporary.replace(destination / "keys.txt")
