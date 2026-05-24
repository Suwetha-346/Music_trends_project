"""
04_diversity_index.py
=====================
Orchestrates the Music Diversity Index pipeline.

Pure computation is delegated to scripts/diversity_core.py (testable,
side-effect-free). This script handles I/O only: load from DB, save
results to CSV and back to DB.

Formula:  H(month) = -sum(p_i * ln(p_i))
Where:    p_i = proportion of plays for artist i in that month

Run after: 02_load_to_db.py
Run before: 05_visualizations.py
"""

import os
import sqlite3
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PATHS, PIPELINE
from logger import get_logger
from scripts.diversity_core import (
    compute_monthly_metrics,
    add_rolling_averages,
    detect_change_points,
)

log = get_logger(__name__)

DB_PATH     = PATHS["db"]
REPORTS_DIR = PATHS["reports"]
os.makedirs(REPORTS_DIR, exist_ok=True)


def load_streams() -> pd.DataFrame:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found. Run 02_load_to_db.py first.")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT s.year, s.month, a.artist_name
        FROM streams s
        JOIN tracks t  ON s.track_id  = t.track_id
        JOIN artists a ON t.artist_id = a.artist_id
        ORDER BY s.year, s.month
    """, conn)
    conn.close()
    log.info("Loaded %s stream records from database", f"{len(df):,}")
    return df


def save_to_db(metrics: pd.DataFrame) -> None:
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM diversity_metrics")

    for _, row in metrics.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO diversity_metrics
            (year, month, total_plays, unique_artists, shannon_entropy,
             normalized_entropy, new_artist_ratio, top1_concentration)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            int(row["year"]), int(row["month"]), int(row["total_plays"]),
            int(row["unique_artists"]), float(row["shannon_entropy"]),
            float(row["normalized_entropy"]), float(row["new_artist_ratio"]),
            float(row["top1_concentration"])
        ))

    conn.commit()
    conn.close()
    log.info("Saved diversity metrics to database")


def log_summary(metrics: pd.DataFrame) -> None:
    log.info("=" * 60)
    log.info("  DIVERSITY INDEX SUMMARY")
    log.info("=" * 60)
    log.info("  Months analyzed:       %d", len(metrics))
    log.info("  Entropy range:         %.3f – %.3f",
             metrics["shannon_entropy"].min(), metrics["shannon_entropy"].max())
    log.info("  Avg Evenness (E):      %.3f", metrics["normalized_entropy"].mean())
    log.info("  Avg New Artist Ratio:  %.1f%%", metrics["new_artist_ratio"].mean() * 100)
    log.info("  Avg Top-1 Conc.:       %.1f%%", metrics["top1_concentration"].mean() * 100)

    log.info("Most diverse months (high Shannon Entropy):")
    for _, row in metrics.nlargest(5, "shannon_entropy").iterrows():
        log.info("  %s  H=%.3f  E=%.3f  Artists=%d",
                 row["year_month"], row["shannon_entropy"],
                 row["normalized_entropy"], int(row["unique_artists"]))

    log.info("Least diverse months:")
    for _, row in metrics.nsmallest(5, "shannon_entropy").iterrows():
        log.info("  %s  H=%.3f  E=%.3f  Artists=%d",
                 row["year_month"], row["shannon_entropy"],
                 row["normalized_entropy"], int(row["unique_artists"]))

    changes = metrics[metrics["is_change_point"] == 1]
    log.info("Significant change points detected: %d", len(changes))
    for _, row in changes.iterrows():
        log.info("  %s  ΔH=%.3f", row["year_month"], row["entropy_delta"])


def main() -> None:
    log.info("=" * 55)
    log.info("  STEP 04 — DIVERSITY INDEX")
    log.info("=" * 55)

    df      = load_streams()
    metrics = compute_monthly_metrics(df)
    log.info("Computed metrics for %d months", len(metrics))

    metrics = add_rolling_averages(metrics, window=PIPELINE["diversity_rolling_window"])
    log.info("Added %d-month rolling averages", PIPELINE["diversity_rolling_window"])

    metrics = detect_change_points(metrics, threshold_std=PIPELINE["change_point_threshold"])
    n_changes = metrics["is_change_point"].sum()
    log.info("Detected %d significant change points", n_changes)

    log_summary(metrics)

    out_csv = os.path.join(REPORTS_DIR, "diversity_metrics.csv")
    metrics.to_csv(out_csv, index=False)
    log.info("CSV saved → %s", out_csv)

    save_to_db(metrics)
    log.info("Next step → run: python scripts/05_visualizations.py")


if __name__ == "__main__":
    main()
