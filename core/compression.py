from __future__ import annotations
import struct
try:
    import lz4.block
except ImportError as exc:
    raise SystemExit("Missing dependency 'lz4'. Install with: pip install lz4") from exc
from .errors import AssetCryptError


def lz4_pack(data: bytes) -> bytes:
    compressed = lz4.block.compress(data, mode="high_compression", store_size=False)
    return struct.pack("<I", len(data)) + compressed


def lz4_unpack(data: bytes) -> bytes:
    if len(data) < 4:
        raise AssetCryptError("LZ4 payload is shorter than its 4-byte size header.")
    expected_size = struct.unpack_from("<I", data, 0)[0]
    try:
        result = lz4.block.decompress(data[4:], uncompressed_size=expected_size)
    except Exception as exc:
        raise AssetCryptError(f"LZ4 decompression failed (declared size {expected_size}).") from exc
    if len(result) != expected_size:
        raise AssetCryptError(f"LZ4 size mismatch: expected {expected_size}, got {len(result)}.")
    return result
