"""Read the benchmark store: one CSV per algorithm in results/store/ (plus the legacy single
results/store.csv while it still exists), with the same precedence as tools/bench.py read_store."""
import csv
from pathlib import Path

KEY = ("algo", "source_sha256", "instance_id")


def load_store_rows(repo) -> list:
    repo = Path(repo)
    files = [repo / "results/store.csv"] + sorted((repo / "results/store").glob("*.csv"))
    rows = {}
    for f in files:
        if f.exists():
            with open(f, newline="", encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    rows[tuple(r[k] for k in KEY)] = r
    return list(rows.values())
