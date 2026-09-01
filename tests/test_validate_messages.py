import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_messages import MAX_CATALOG_SIZE_BYTES, validate


ROOT = Path(__file__).resolve().parents[1]


class ValidateMessagesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = json.loads((ROOT / "messages.json").read_text(encoding="utf-8"))

    def validate_catalog(self, catalog: dict) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "messages.json"
            path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
            return validate(path)

    def test_accepts_current_catalog(self) -> None:
        self.assertEqual([], self.validate_catalog(self.catalog))

    def test_rejects_boolean_version(self) -> None:
        self.catalog["version"] = True

        self.assertIn(
            "version must be the integer 1.",
            self.validate_catalog(self.catalog),
        )

    def test_rejects_non_canonical_date(self) -> None:
        self.catalog["updatedAt"] = "20260826"

        self.assertIn(
            "updatedAt must use YYYY-MM-DD.",
            self.validate_catalog(self.catalog),
        )

    def test_rejects_unicode_digits_in_id(self) -> None:
        self.catalog["categories"]["keep_going"][0]["id"] = "keep-going-١٢٣"

        errors = self.validate_catalog(self.catalog)

        self.assertTrue(any(".id has an invalid format." in error for error in errors))

    def test_rejects_oversized_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "messages.json"
            path.write_bytes(b" " * (MAX_CATALOG_SIZE_BYTES + 1))

            self.assertEqual(
                [f"Catalog must not exceed {MAX_CATALOG_SIZE_BYTES} bytes."],
                validate(path),
            )


if __name__ == "__main__":
    unittest.main()
