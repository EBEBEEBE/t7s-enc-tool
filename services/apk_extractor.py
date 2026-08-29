from __future__ import annotations

import io
import zipfile
from pathlib import Path

from core import AssetCryptError, Keys

METADATA_PATH = "assets/bin/Data/Managed/Metadata/global-metadata.dat"
BASE_APK_NAME = "jp.ne.donuts.t7s.apk"
FIELDS = {
    "V1AESKey": (0x038F9F, 16),
    "V2Key": (0x0612D7, 16),
    "V2Signature": (0x0AE2F2, 7),
    "HMACKey": (0x0612C7, 16),
}


class ApkKeyExtractor:
    @staticmethod
    def _read_metadata_from_apk(apk_source) -> bytes:
        with zipfile.ZipFile(apk_source, "r") as apk:
            return apk.read(METADATA_PATH)

    @classmethod
    def read_metadata(cls, input_path: Path) -> bytes:
        if input_path.suffix.lower() != ".xapk":
            return cls._read_metadata_from_apk(input_path)
        with zipfile.ZipFile(input_path, "r") as xapk:
            names = xapk.namelist()
            candidates = [name for name in names if name.rsplit("/", 1)[-1] == BASE_APK_NAME]
            if not candidates:
                candidates = [name for name in names if name.lower().endswith(".apk")]
            for name in candidates:
                try:
                    return cls._read_metadata_from_apk(io.BytesIO(xapk.read(name)))
                except (KeyError, zipfile.BadZipFile):
                    continue
        raise AssetCryptError(f"Could not find an APK containing {METADATA_PATH} inside the XAPK.")

    @classmethod
    def extract(cls, input_path: Path) -> Keys:
        if input_path.suffix.lower() not in {".apk", ".xapk"}:
            raise AssetCryptError("Please select an APK or XAPK file.")
        try:
            metadata = cls.read_metadata(input_path)
        except (FileNotFoundError, zipfile.BadZipFile, KeyError, OSError) as exc:
            raise AssetCryptError(f"Could not read APK/XAPK: {exc}") from exc
        values = {}
        for name, (offset, length) in FIELDS.items():
            raw = metadata[offset:offset + length]
            if len(raw) != length:
                raise AssetCryptError(f"{name} offset is outside global-metadata.dat.")
            try:
                values[name] = raw.decode("ascii")
            except UnicodeDecodeError as exc:
                raise AssetCryptError(f"{name} at offset 0x{offset:X} is not valid ASCII. This APK version may use different offsets.") from exc
        keys = Keys(values["V1AESKey"].encode(), values["V2Key"].encode(), values["V2Signature"].encode(), values["HMACKey"].encode())
        from .keys import KeyService
        KeyService.validate(keys)
        return keys
