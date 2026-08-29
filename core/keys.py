from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .errors import AssetCryptError


def _encode_optional(value: Optional[str]) -> Optional[bytes]:
    return None if value is None else value.encode("utf-8")


@dataclass
class Keys:
    v1_aes_key: Optional[bytes] = None
    v2_raw_key: Optional[bytes] = None
    v2_signature: Optional[bytes] = None
    hmac_key: Optional[bytes] = None

    @classmethod
    def from_file(cls, path: Path) -> "Keys":
        if not path.is_file():
            raise AssetCryptError(f"Key file not found: {path}")
        values: dict[str, str] = {}
        aliases = {"v1aeskey": "v1_aes_key", "v2key": "v2_raw_key", "v2signature": "v2_signature", "hmackey": "hmac_key"}
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            if "=" not in line:
                raise AssetCryptError(f"{path}:{line_number}: expected 'Name = value'")
            name, value = line.split("=", 1)
            name = name.strip().lower()
            if name in aliases:
                values[aliases[name]] = value.strip()
        return cls(**{field: _encode_optional(values.get(field)) for field in ("v1_aes_key", "v2_raw_key", "v2_signature", "hmac_key")})

    def require_v1(self) -> bytes:
        if self.v1_aes_key is None:
            raise AssetCryptError("V1AESKey is required for Version 1.")
        if len(self.v1_aes_key) != 16:
            raise AssetCryptError(f"V1AESKey must be 16 bytes; got {len(self.v1_aes_key)}.")
        return self.v1_aes_key

    def require_v2_key(self) -> bytes:
        if self.v2_raw_key is None:
            raise AssetCryptError("V2Key is required for Version 2.")
        if len(self.v2_raw_key) != 16:
            raise AssetCryptError(f"V2Key must be 16 bytes; got {len(self.v2_raw_key)}.")
        return shuffle_v2_key(self.v2_raw_key)

    def require_signature(self) -> bytes:
        if self.v2_signature is None:
            raise AssetCryptError("V2Signature is required for Version 2.")
        if not self.v2_signature:
            raise AssetCryptError("V2Signature cannot be empty.")
        return self.v2_signature

    def require_hmac(self) -> bytes:
        if self.hmac_key is None:
            raise AssetCryptError("HMACKey is required to generate Version 2 filenames.")
        return self.hmac_key


def shuffle_v2_key(raw_key: bytes) -> bytes:
    if len(raw_key) != 16:
        raise AssetCryptError("V2 raw key must be exactly 16 bytes.")
    return bytes(byte ^ (37 + 13 * i) for i, byte in enumerate(raw_key))
