from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from .compression import lz4_pack, lz4_unpack
from .crypto import aes_cbc_decrypt, aes_cbc_encrypt
from .detection import auto_lz4_for_path, choose_mode, detect_version_from_filename
from .errors import AssetCryptError
from .keys import Keys
from .naming import default_decrypted_name, default_encrypted_name


@dataclass
class ProcessResult:
    source_path: Path
    output_path: Path
    action: str
    requested_mode: str | None
    resolved_mode: str
    input_size: int | None = None
    output_size: int | None = None
    success: bool = False
    error: str | None = None


def decrypt_bytes(blob: bytes, version: str, use_lz4: bool, keys: Keys) -> bytes:
    if version == "v1":
        if len(blob) <= 16: raise AssetCryptError("Version 1 input is too short.")
        iv, ciphertext = blob[:16], blob[16:]
        plaintext = aes_cbc_decrypt(ciphertext, keys.require_v1(), iv)
    elif version == "v2":
        signature = keys.require_signature()
        if len(blob) < len(signature) + 32: raise AssetCryptError("Version 2 input is too short.")
        if not blob.startswith(signature): raise AssetCryptError(f"Version 2 signature mismatch; expected {signature!r}.")
        start = len(signature)
        plaintext = aes_cbc_decrypt(blob[start + 16:], keys.require_v2_key(), blob[start:start + 16])
    else:
        raise AssetCryptError(f"Unknown encryption version: {version}")
    return lz4_unpack(plaintext) if use_lz4 else plaintext


def encrypt_bytes(data: bytes, version: str, use_lz4: bool, keys: Keys) -> bytes:
    payload = lz4_pack(data) if use_lz4 else data
    iv = os.urandom(16)
    if version == "v1": return iv + aes_cbc_encrypt(payload, keys.require_v1(), iv)
    if version == "v2":
        signature = keys.require_signature()
        return signature + iv + aes_cbc_encrypt(payload, keys.require_v2_key(), iv)
    raise AssetCryptError(f"Unknown encryption version: {version}")


def extract_iv(blob: bytes, version: str, keys: Keys | None = None) -> bytes:
    if version == "v1":
        if len(blob) < 16: raise AssetCryptError("Version 1 input is too short.")
        return blob[:16]
    if version == "v2":
        if keys is None: raise AssetCryptError("Keys are required to inspect a Version 2 IV.")
        signature = keys.require_signature()
        if len(blob) < len(signature) + 16 or not blob.startswith(signature): raise AssetCryptError("Invalid Version 2 input signature.")
        return blob[len(signature):len(signature) + 16]
    raise AssetCryptError(f"Unknown encryption version: {version}")


def collect_inputs(input_path: Path, command: str, auto: bool) -> tuple[list[Path], Path]:
    if input_path.is_file():
        if auto: root, candidates = input_path.parent, (p for p in input_path.parent.rglob("*") if p.is_file())
        else: return [input_path], input_path.parent
    elif input_path.is_dir(): root, candidates = input_path, (p for p in input_path.rglob("*") if p.is_file())
    else: raise AssetCryptError(f"Input does not exist: {input_path}")
    files = [p for p in candidates if not auto or (p.suffix.lower() == ".enc" if command == "decrypt" else p.suffix.lower() != ".enc")]
    files.sort()
    return files, root


def output_mode(output: Path | None, multiple: bool) -> str:
    if output is None: return "default"
    raw = str(output)
    if (output.exists() and output.is_dir()) or raw.endswith(("/", "\\")): return "directory"
    return "prefix" if multiple else "file"


def build_output_path(source: Path, root: Path, output: Path | None, multiple: bool, command: str, version: str, keys: Keys) -> Path:
    mode = output_mode(output, multiple)
    if mode == "file":
        assert output is not None
        return output
    generated = default_decrypted_name(source, version) if command == "decrypt" else default_encrypted_name(source, version, keys)
    try: rel_parent = source.parent.relative_to(root)
    except ValueError: rel_parent = Path()
    if mode == "default": return source.parent / generated
    assert output is not None
    if mode == "directory": return output / rel_parent / generated
    return output.parent / rel_parent / f"{output.name}{generated}"


def process_one(source: Path, destination: Path, command: str, version: str, use_lz4: bool, keys: Keys) -> None:
    if source.resolve() == destination.resolve(): raise AssetCryptError(f"Refusing to overwrite input in-place: {source}")
    blob = source.read_bytes()
    result = decrypt_bytes(blob, version, use_lz4, keys) if command == "decrypt" else encrypt_bytes(blob, version, use_lz4, keys)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(result)


def process_file(
    source: Path,
    destination: Path,
    command: str,
    keys: Keys,
    requested_mode: str | None = None,
) -> ProcessResult:
    """Process one file and return a result suitable for CLI or GUI reporting."""
    input_size = source.stat().st_size
    version, use_lz4 = choose_mode(source, command, requested_mode)
    resolved_mode = format_mode(version, use_lz4)
    result = ProcessResult(source, destination, command, requested_mode, resolved_mode, input_size=input_size)
    try:
        process_one(source, destination, command, version, use_lz4, keys)
        result.success = True
        result.output_size = destination.stat().st_size
    except Exception as exc:
        result.error = str(exc)
    return result


def format_mode(version: str, use_lz4: bool) -> str:
    return "v2z" if version == "v2" and use_lz4 else version
