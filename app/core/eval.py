import json
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


def _iter_json_lines(path: Path) -> Iterable[Tuple[int, Dict[str, Any]]]:
    if not path.exists():
        return []
    lines = []
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            lines.append((idx, json.loads(stripped)))
    return lines


def _evaluate_record(record: Dict[str, Any]) -> bool:
    if "ok" in record:
        return bool(record["ok"])
    if "expected" in record and "got" in record:
        return record["got"] == record["expected"]
    return True


def _write_reports(out_dir: Path, records: Iterable[Dict[str, Any]]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "reports.jsonl"
    with report_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_eval(evalset: str, rules: str, out_dir: str, ledger: str) -> Dict[str, Any]:
    evalset_path = Path(evalset)
    records = []
    passed = 0
    total = 0
    for _, record in _iter_json_lines(evalset_path):
        ok = _evaluate_record(record)
        record = {**record, "ok": ok}
        records.append(record)
        total += 1
        if ok:
            passed += 1

    _write_reports(Path(out_dir), records)

    ledger_path = Path(ledger)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    if not ledger_path.exists():
        ledger_path.touch()

    pass_rate = float(passed / total) if total else 0.0
    return {
        "total": total,
        "passed": passed,
        "pass_rate": pass_rate,
        "ok": passed == total,
        "evalset": str(evalset_path),
        "rules": rules,
        "out": out_dir,
        "ledger": str(ledger_path),
    }
