"""
run_all.py — Run the full pipeline end-to-end.
Usage: python run_all.py
"""

import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import PATHS
from logger import get_logger

log = get_logger(__name__)

BASE    = PATHS["base"]
SCRIPTS = PATHS["scripts"]

STEPS = [
    ("Generate Synthetic Data",  os.path.join(BASE,    "generate_synthetic_data.py")),
    ("01 — Data Cleaning",       os.path.join(SCRIPTS, "01_data_cleaning.py")),
    ("02 — Load to Database",    os.path.join(SCRIPTS, "02_load_to_db.py")),
    ("03 — Analysis Queries",    os.path.join(SCRIPTS, "03_analysis_queries.py")),
    ("04 — Diversity Index",     os.path.join(SCRIPTS, "04_diversity_index.py")),
    ("05 — Visualizations",      os.path.join(SCRIPTS, "05_visualizations.py")),
]


def main() -> None:
    log.info("=" * 55)
    log.info("  SPOTIFY MUSIC EVOLUTION — FULL PIPELINE")
    log.info("=" * 55)

    for label, script in STEPS:
        log.info("RUNNING: %s", label)
        result = subprocess.run([sys.executable, script], cwd=BASE)
        if result.returncode != 0:
            log.error("Pipeline failed at step: %s", label)
            sys.exit(1)
        log.info("DONE: %s", label)

    log.info("=" * 55)
    log.info("  PIPELINE COMPLETE!")
    log.info("  Charts  → output/charts/")
    log.info("  Reports → output/reports/")
    log.info("  Logs    → output/logs/pipeline.log")
    log.info("=" * 55)


if __name__ == "__main__":
    main()
