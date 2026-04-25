import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestV072Baseline(unittest.TestCase):
    def test_smoke_and_counts(self):
        base_dir = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            outdir = Path(td)
            cmd = [
                "python",
                "motor_v072.py",
                "--pdf",
                "input/P02_06 - PMI - CONSTRUTORA MALLMANN.pdf",
                "--page",
                "0",
                "--view",
                "240,450,1160,1640",
                "--origin",
                "280,1600",
                "--outdir",
                str(outdir),
                "--name",
                "baseline_test",
            ]
            subprocess.run(cmd, cwd=base_dir, check=True)

            dxf = outdir / "baseline_test.dxf"
            svg = outdir / "baseline_test.svg"
            report_path = outdir / "baseline_test_relatorio.json"

            self.assertTrue(dxf.exists(), "DXF não gerado")
            self.assertTrue(svg.exists(), "SVG não gerado")
            self.assertTrue(report_path.exists(), "Relatório JSON não gerado")

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["motor"], "V07.2 Clean Native Export")
            self.assertEqual(report["dxf_format"], "R12 / AC1009")
            self.assertEqual(report["final_lines"], 8654)
            self.assertEqual(report["layers"]["A-WALL"], 2951)
            self.assertEqual(report["layers"]["A-REF"], 5703)


if __name__ == "__main__":
    unittest.main()
