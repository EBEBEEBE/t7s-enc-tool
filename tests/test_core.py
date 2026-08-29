import unittest
from pathlib import Path

from core import Keys, decrypt_bytes, encrypt_bytes, extract_iv, process_file
from core.detection import auto_lz4_for_path, choose_mode, detect_version_from_filename
from core.errors import AssetCryptError
from core.naming import default_encrypted_name, split_v2_plain_name


KEYS = Keys(b"0123456789abcdef", b"fedcba9876543210", b"t7s-enc", b"hmac-secret")


class TestCore(unittest.TestCase):
    def test_round_trip_all_formats(self):
        data = b"hello asset crypt\x00" * 20
        for version, use_lz4 in (("v1", False), ("v2", False), ("v2", True)):
            with self.subTest(version=version, use_lz4=use_lz4):
                encrypted = encrypt_bytes(data, version, use_lz4, KEYS)
                self.assertEqual(decrypt_bytes(encrypted, version, use_lz4, KEYS), data)

    def test_v2_has_signature_and_extractable_iv(self):
        blob = encrypt_bytes(b"payload", "v2", False, KEYS)
        self.assertTrue(blob.startswith(b"t7s-enc"))
        self.assertEqual(len(extract_iv(blob, "v2", KEYS)), 16)

    def test_auto_detection_and_lz4_rules(self):
        self.assertEqual(detect_version_from_filename(Path("foo.jpg.enc")), "v1")
        self.assertEqual(detect_version_from_filename(Path("foo_" + "A" * 64 + ".jpg.enc")), "v2")
        self.assertEqual(choose_mode(Path("data.json"), "encrypt", None), ("v2", True))
        self.assertFalse(auto_lz4_for_path(Path("photo.png"), False))

    def test_v2_name_round_trip(self):
        encrypted_name = default_encrypted_name(Path("foo.jpg"), "v2", KEYS)
        self.assertEqual(split_v2_plain_name(Path(encrypted_name)), "foo.jpg")

    def test_wrong_signature_is_rejected(self):
        with self.assertRaisesRegex(AssetCryptError, "signature mismatch"):
            decrypt_bytes(b"wrong!!" + b"\x00" * 32, "v2", False, KEYS)

    def test_process_file_returns_structured_result(self):
        source = Path("tests") / "_process_source.bin"
        destination = Path("tests") / "_process_output.enc"
        try:
            source.write_bytes(b"process me")
            result = process_file(source, destination, "encrypt", KEYS, "v2")
            self.assertTrue(result.success)
            self.assertEqual(result.resolved_mode, "v2")
            self.assertEqual(result.input_size, 10)
            self.assertGreater(result.output_size, result.input_size)
        finally:
            source.unlink(missing_ok=True)
            destination.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
