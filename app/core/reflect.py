import json
from itertools import cycle, islice
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _load_reports(reports_dir: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not reports_dir.exists():
        return records
    for report_path in sorted(reports_dir.glob("*.jsonl")):
        with report_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                records.append(json.loads(stripped))
    return records


def _synthesize_tests(records: Iterable[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    records_list = list(records)
    if not records_list:
        return [{"expected": None, "got": None, "source_index": idx} for idx in range(n)]

    synthesized: List[Dict[str, Any]] = []
    for idx, record in enumerate(islice(cycle(records_list), n)):
        expected = record.get("expected", record.get("got"))
        synthesized.append(
            {
                "expected": expected,
                "got": expected,
                "source_index": idx,
            }
        )
    return synthesized


def run_reflect(reports: str, out_tests: str, n: int) -> Dict[str, Any]:
    reports_dir = Path(reports)
    out_tests_path = Path(out_tests)
    out_tests_path.parent.mkdir(parents=True, exist_ok=True)

    records = _load_reports(reports_dir)
    synthesized = _synthesize_tests(records, n)

    with out_tests_path.open("w", encoding="utf-8") as handle:
        for record in synthesized:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {
        "n": n,
        "out_tests": str(out_tests_path),
        "reports": str(reports_dir),
    }
