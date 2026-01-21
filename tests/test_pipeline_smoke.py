import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

YAML_AVAILABLE = importlib.util.find_spec("yaml") is not None


@unittest.skipUnless(YAML_AVAILABLE, "pyyaml is required for CLI smoke tests")
class TestPipelineSmoke(unittest.TestCase):
    def setUp(self):
        self.root = ROOT
        self.env = os.environ.copy()
        src_path = str(self.root / "src")
        self.env["PYTHONPATH"] = os.pathsep.join(
            [src_path, self.env.get("PYTHONPATH", "")]
        ).strip(os.pathsep)

    def test_pipeline_smoke(self):
        eval_file = self.root / "domains" / "finance_cashflow" / "eval" / "seed_test.jsonl"
        rules_file = self.root / "rulesets" / "seed_rules.yaml"
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "pipeline"
            ledger_path = Path(tmpdir) / "ledger" / "runs.sqlite"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agiwb.cli",
                    "pipeline",
                    "--seed",
                    str(eval_file),
                    "--seed-rules",
                    str(rules_file),
                    "--out-dir",
                    str(out_dir),
                    "--ledger",
                    str(ledger_path),
                    "--n",
                    "3",
                ],
                env=self.env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((out_dir / "summary.json").exists())
            self.assertTrue((out_dir / "seed" / "summary.json").exists())
            self.assertTrue((out_dir / "round2" / "summary.json").exists())
            self.assertTrue((out_dir / "synth_tests.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
