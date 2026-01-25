import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

YAML_AVAILABLE = importlib.util.find_spec("yaml") is not None
if YAML_AVAILABLE:
    import agiwb.cli  # noqa: E402


@unittest.skipUnless(YAML_AVAILABLE, "pyyaml is required for CLI smoke tests")
class TestCliSmoke(unittest.TestCase):
    def setUp(self):
        self.root = ROOT
        self.env = os.environ.copy()
        src_path = str(self.root / "src")
        self.env["PYTHONPATH"] = os.pathsep.join(
            [src_path, self.env.get("PYTHONPATH", "")]
        ).strip(os.pathsep)

    def test_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "agiwb.cli", "--help"],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_eval_smoke(self):
        eval_file = self.root / "domains" / "finance_cashflow" / "eval" / "seed_test.jsonl"
        rules_file = self.root / "rulesets" / "seed_rules.yaml"
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "reports"
            ledger_path = Path(tmpdir) / "ledger" / "runs.sqlite"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agiwb.cli",
                    "eval",
                    "--eval-file",
                    str(eval_file),
                    "--rules",
                    str(rules_file),
                    "--out",
                    str(out_dir),
                    "--ledger",
                    str(ledger_path),
                ],
                env=self.env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            summary_path = out_dir / "summary.json"
            self.assertTrue(summary_path.exists())
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["total"], 2)

if __name__ == "__main__":
    unittest.main()
