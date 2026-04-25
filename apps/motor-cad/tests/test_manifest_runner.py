import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestManifestRunner(unittest.TestCase):
    def test_manifest_executes_and_matches_baseline_counts(self):
        base_dir = Path(__file__).resolve().parents[1]
        manifest_src = base_dir / "manifests" / "mallmann_baseline_manifest.json"
        manifest = json.loads(manifest_src.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as td:
            outdir = Path(td)
            manifest["output_root"] = str(outdir)
            manifest["documents"][0]["output_dir"] = str(outdir)
            manifest["documents"][0]["pages"][0]["regions"][0]["output_name"] = "manifest_baseline_test"
            tmp_manifest = outdir / "manifest.json"
            tmp_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

            subprocess.run(
                ["python", "run_manifest.py", "--manifest", str(tmp_manifest)],
                cwd=base_dir,
                check=True,
            )

            report_path = outdir / "manifest_baseline_test_relatorio.json"
            summary_path = outdir / "mallmann_pmi_manifest_run.json"
            self.assertTrue(report_path.exists(), "Relatório por região não foi gerado")
            self.assertTrue(summary_path.exists(), "Resumo de execução do manifesto não foi gerado")

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["final_lines"], 8654)
            self.assertEqual(report["layers"]["A-WALL"], 2951)
            self.assertEqual(report["layers"]["A-REF"], 5703)
            self.assertIn("manifest", report)
            self.assertEqual(report["manifest"]["project_id"], "mallmann_pmi")


if __name__ == "__main__":
    unittest.main()
