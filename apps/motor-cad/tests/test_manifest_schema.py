import json
import unittest
from pathlib import Path


class TestInputManifestSchemaV01(unittest.TestCase):
    def test_schema_file_exists_and_declares_v01(self):
        base_dir = Path(__file__).resolve().parents[1]
        schema_path = base_dir / "docs" / "schemas" / "input_manifest.schema.json"
        self.assertTrue(schema_path.exists(), "Schema do manifesto não encontrado")

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema.get("title"), "Motor CAD Input Manifest v0.1")
        self.assertEqual(schema.get("type"), "object")

    def test_mallmann_manifest_matches_required_contract(self):
        base_dir = Path(__file__).resolve().parents[1]
        manifest_path = base_dir / "manifests" / "mallmann_baseline_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertIn("documents", manifest)
        self.assertIsInstance(manifest["documents"], list)
        self.assertGreater(len(manifest["documents"]), 0)

        for doc in manifest["documents"]:
            self.assertIn("source_pdf", doc)
            self.assertIsInstance(doc["source_pdf"], str)
            self.assertTrue(doc["source_pdf"].strip())

            self.assertIn("pages", doc)
            self.assertIsInstance(doc["pages"], list)
            self.assertGreater(len(doc["pages"]), 0)

            for page in doc["pages"]:
                self.assertIn("page_index", page)
                self.assertIsInstance(page["page_index"], int)

                self.assertIn("regions", page)
                self.assertIsInstance(page["regions"], list)
                self.assertGreater(len(page["regions"]), 0)

                for region in page["regions"]:
                    self.assertIn("bbox", region)
                    self.assertIsInstance(region["bbox"], list)
                    self.assertEqual(len(region["bbox"]), 4)
                    self.assertTrue(all(isinstance(v, (int, float)) for v in region["bbox"]))

                    self.assertIn("origin", region)
                    self.assertIsInstance(region["origin"], list)
                    self.assertEqual(len(region["origin"]), 2)
                    self.assertTrue(all(isinstance(v, (int, float)) for v in region["origin"]))


if __name__ == "__main__":
    unittest.main()
