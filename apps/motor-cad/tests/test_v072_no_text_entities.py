import subprocess
import tempfile
import unittest
from pathlib import Path


class TestV072NoTextEntities(unittest.TestCase):
    def test_dxf_has_no_text_entity(self):
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
                "baseline_text_check",
            ]
            subprocess.run(cmd, cwd=base_dir, check=True)

            dxf = (outdir / "baseline_text_check.dxf").read_text(encoding="utf-8")
            self.assertNotIn("\nTEXT\n", dxf)


if __name__ == "__main__":
    unittest.main()
