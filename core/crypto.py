from __future__ import annotations
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.padding import PKCS7
except ImportError as exc:
    raise SystemExit("Missing dependency 'cryptography'. Install with: pip install cryptography") from exc
from .errors import AssetCryptError


def aes_cbc_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    padder = PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def aes_cbc_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    if len(data) == 0 or len(data) % 16 != 0:
        raise AssetCryptError("Ciphertext size is not a non-zero multiple of the AES block size.")
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(data) + decryptor.finalize()
    try:
        unpadder = PKCS7(128).unpadder()
        return unpadder.update(padded) + unpadder.finalize()
    except ValueError as exc:
        raise AssetCryptError("Invalid PKCS#7 padding. The key/version is probably wrong.") from exc
