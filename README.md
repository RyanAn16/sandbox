# AGI Workbench

AGI Workbench provides a lightweight rule evaluation CLI for JSONL eval sets.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Run the CLI:

```bash
python -m agiwb.cli --help
python -m agiwb.cli eval \
  --eval-file domains/finance_cashflow/eval/seed_test.jsonl \
  --rules rulesets/seed_rules.yaml \
  --out data/reports \
  --ledger data/ledger/runs.sqlite
```

Legacy compatibility:

```bash
python -m app.cli --help
```

Incremental rules default to `rulesets/incremental_rules.yaml` when
`--write-incremental` is supplied.
