import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.eval import run_eval
from app.core.reflect import run_reflect


@dataclass
class PipelineConfig:
    run_id: str
    timestamp: str
    seed_evalset: str
    seed_rules: str
    seed_out: str
    seed_ledger: str
    reflect_reports: str
    reflect_out_tests: str
    reflect_n: int
    round2_evalset: str
    round2_rules: str
    round2_out: str
    round2_ledger: str
    outdir: str
    strict: bool


def _get_git_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "nogit"


def _extract_domain(seed_evalset: str) -> str:
    parts = Path(seed_evalset).parts
    if "domains" in parts:
        idx = parts.index("domains")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return "unknown"


def _build_config(
    *,
    seed_evalset: Optional[str],
    seed_rules: Optional[str],
    seed_out: Optional[str],
    seed_ledger: Optional[str],
    reflect_reports: Optional[str],
    reflect_out_tests: Optional[str],
    reflect_n: Optional[int],
    round2_evalset: Optional[str],
    round2_rules: Optional[str],
    round2_out: Optional[str],
    round2_ledger: Optional[str],
    outdir: Optional[str],
    strict: bool,
) -> PipelineConfig:
    defaults = {
        "seed_evalset": "domains/finance_cashflow/eval/seed_test.jsonl",
        "seed_rules": "assets/rules/seed_rules.yaml",
        "seed_out": "reports",
        "seed_ledger": "ledger/ledger.sqlite",
        "reflect_reports": "reports",
        "reflect_out_tests": "reports/synth_tests.jsonl",
        "reflect_n": 13,
        "round2_evalset": "reports/synth_tests.jsonl",
        "round2_rules": "assets/rules/seed_rules.yaml",
        "round2_out": "reports_round2",
        "round2_ledger": "ledger/ledger_round2.sqlite",
    }

    now = datetime.now()
    domain = _extract_domain(seed_evalset or defaults["seed_evalset"])
    run_id = f"{now.strftime('%Y%m%d_%H%M%S')}_{domain}_{_get_git_sha()}"
    resolved_outdir = outdir or str(Path("reports") / run_id)

    resolved_seed_out = seed_out or defaults["seed_out"]
    resolved_reflect_reports = reflect_reports or defaults["reflect_reports"]
    resolved_reflect_out_tests = reflect_out_tests or defaults["reflect_out_tests"]
    resolved_round2_out = round2_out or defaults["round2_out"]

    outdir_specified = outdir is not None
    if outdir_specified:
        resolved_seed_out = str(Path(resolved_outdir) / "seed_eval")
        resolved_reflect_out_tests = str(Path(resolved_outdir) / "synth_tests.jsonl")
        resolved_reflect_reports = resolved_seed_out
        resolved_round2_out = str(Path(resolved_outdir) / "round2_eval")

    if round2_evalset is None:
        resolved_round2_evalset = resolved_reflect_out_tests
    else:
        resolved_round2_evalset = round2_evalset

    return PipelineConfig(
        run_id=run_id,
        timestamp=now.isoformat(timespec="seconds"),
        seed_evalset=seed_evalset or defaults["seed_evalset"],
        seed_rules=seed_rules or defaults["seed_rules"],
        seed_out=resolved_seed_out,
        seed_ledger=seed_ledger or defaults["seed_ledger"],
        reflect_reports=resolved_reflect_reports,
        reflect_out_tests=resolved_reflect_out_tests,
        reflect_n=reflect_n if reflect_n is not None else defaults["reflect_n"],
        round2_evalset=resolved_round2_evalset,
        round2_rules=round2_rules or defaults["round2_rules"],
        round2_out=resolved_round2_out,
        round2_ledger=round2_ledger or defaults["round2_ledger"],
        outdir=resolved_outdir,
        strict=strict,
    )


def run_pipeline(
    *,
    seed_evalset: Optional[str],
    seed_rules: Optional[str],
    seed_out: Optional[str],
    seed_ledger: Optional[str],
    reflect_reports: Optional[str],
    reflect_out_tests: Optional[str],
    reflect_n: Optional[int],
    round2_evalset: Optional[str],
    round2_rules: Optional[str],
    round2_out: Optional[str],
    round2_ledger: Optional[str],
    outdir: Optional[str],
    strict: bool,
) -> Dict[str, Any]:
    config = _build_config(
        seed_evalset=seed_evalset,
        seed_rules=seed_rules,
        seed_out=seed_out,
        seed_ledger=seed_ledger,
        reflect_reports=reflect_reports,
        reflect_out_tests=reflect_out_tests,
        reflect_n=reflect_n,
        round2_evalset=round2_evalset,
        round2_rules=round2_rules,
        round2_out=round2_out,
        round2_ledger=round2_ledger,
        outdir=outdir,
        strict=strict,
    )

    seed_eval = run_eval(
        evalset=config.seed_evalset,
        rules=config.seed_rules,
        out_dir=config.seed_out,
        ledger=config.seed_ledger,
    )
    reflect = run_reflect(
        reports=config.reflect_reports,
        out_tests=config.reflect_out_tests,
        n=config.reflect_n,
    )
    round2_eval = run_eval(
        evalset=config.round2_evalset,
        rules=config.round2_rules,
        out_dir=config.round2_out,
        ledger=config.round2_ledger,
    )

    domain = _extract_domain(config.seed_evalset)
    summary = {
        "run_id": config.run_id,
        "timestamp": config.timestamp,
        "domain": domain,
        "seed_eval": {
            "total": seed_eval["total"],
            "passed": seed_eval["passed"],
            "pass_rate": seed_eval["pass_rate"],
        },
        "round2_eval": {
            "total": round2_eval["total"],
            "passed": round2_eval["passed"],
            "pass_rate": round2_eval["pass_rate"],
        },
        "reflect": {
            "n": reflect["n"],
            "out_tests": reflect["out_tests"],
        },
        "paths": {
            "outdir": config.outdir,
            "seed_out": config.seed_out,
            "round2_out": config.round2_out,
        },
    }

    outdir_path = Path(config.outdir)
    outdir_path.mkdir(parents=True, exist_ok=True)
    summary_path = outdir_path / "summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)

    rules_snapshot_dir = outdir_path / "rules_snapshot"
    rules_snapshot_dir.mkdir(parents=True, exist_ok=True)
    seed_rules_path = Path(config.seed_rules)
    if seed_rules_path.exists():
        snapshot_path = rules_snapshot_dir / seed_rules_path.name
        snapshot_path.write_bytes(seed_rules_path.read_bytes())

    if config.strict and (not seed_eval["ok"] or not round2_eval["ok"]):
        raise RuntimeError("pipeline strict mode failed")

    summary["summary_path"] = str(summary_path)
    return summary
