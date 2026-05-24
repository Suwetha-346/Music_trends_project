"""
03_analysis_queries.py
======================
Runs SQL queries against the database and exports results as CSVs.

Run after: 02_load_to_db.py
Run before: 05_visualizations.py
"""

import os
import sqlite3
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PATHS
from logger import get_logger

log = get_logger(__name__)

DB_PATH     = PATHS["db"]
REPORTS_DIR = PATHS["reports"]
os.makedirs(REPORTS_DIR, exist_ok=True)


def get_conn():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}\nRun 02_load_to_db.py first.")
    return sqlite3.connect(DB_PATH)


def run_query(conn, name: str, sql: str) -> pd.DataFrame:
    df = pd.read_sql_query(sql, conn)
    out = os.path.join(REPORTS_DIR, f"{name}.csv")
    df.to_csv(out, index=False)
    log.info("  %-35s → %s rows saved", name, f"{len(df):>5,}")
    return df


QUERIES = {
    "top_artists_by_year": """
        WITH yearly_totals AS (
            SELECT a.artist_name, s.year,
                   COUNT(*)                        AS total_plays,
                   ROUND(SUM(s.minutes_played), 1) AS total_minutes
            FROM streams s
            JOIN tracks t  ON s.track_id  = t.track_id
            JOIN artists a ON t.artist_id = a.artist_id
            GROUP BY a.artist_name, s.year
        ),
        ranked AS (
            SELECT yt.*,
                   (SELECT COUNT(*) FROM yearly_totals yt2
                    WHERE yt2.year = yt.year AND yt2.total_minutes > yt.total_minutes) + 1
                   AS rank_in_year
            FROM yearly_totals yt
        )
        SELECT artist_name, year, total_plays, total_minutes, rank_in_year
        FROM ranked WHERE rank_in_year <= 10
        ORDER BY year, rank_in_year
    """,
    "monthly_listening_hours": """
        SELECT year, month,
               COUNT(*)                           AS total_plays,
               ROUND(SUM(minutes_played) / 60, 2) AS total_hours,
               ROUND(AVG(minutes_played), 3)       AS avg_minutes_per_play,
               year || '-' || PRINTF('%02d', month) AS year_month
        FROM streams GROUP BY year, month ORDER BY year, month
    """,
    "hourly_distribution": """
        SELECT hour,
               COUNT(*)                            AS total_plays,
               ROUND(SUM(minutes_played) / 60, 2)  AS total_hours,
               ROUND(AVG(minutes_played), 3)        AS avg_minutes
        FROM streams GROUP BY hour ORDER BY hour
    """,
    "day_of_week_pattern": """
        SELECT day_of_week,
               CASE day_of_week
                   WHEN 0 THEN 'Monday'   WHEN 1 THEN 'Tuesday'
                   WHEN 2 THEN 'Wednesday' WHEN 3 THEN 'Thursday'
                   WHEN 4 THEN 'Friday'   WHEN 5 THEN 'Saturday'
                   WHEN 6 THEN 'Sunday'
               END AS day_name,
               COUNT(*)                            AS total_plays,
               ROUND(SUM(minutes_played) / 60, 2)  AS total_hours
        FROM streams GROUP BY day_of_week ORDER BY day_of_week
    """,
    "hour_day_heatmap": """
        SELECT hour, day_of_week,
               COUNT(*)                           AS total_plays,
               ROUND(SUM(minutes_played)/60, 2)   AS total_hours
        FROM streams GROUP BY hour, day_of_week ORDER BY day_of_week, hour
    """,
    "platform_usage": """
        SELECT year, platform,
               COUNT(*)                           AS total_plays,
               ROUND(SUM(minutes_played)/60, 2)   AS total_hours
        FROM streams WHERE platform IS NOT NULL
        GROUP BY year, platform ORDER BY year, total_plays DESC
    """,
    "skip_rate_trend": """
        SELECT year, month,
               year || '-' || PRINTF('%02d', month) AS year_month,
               COUNT(*)                              AS total_plays,
               SUM(skipped)                          AS skipped_plays,
               ROUND(100.0 * SUM(skipped) / COUNT(*), 2) AS skip_rate_pct
        FROM streams GROUP BY year, month ORDER BY year, month
    """,
    "artist_discovery_per_month": """
        WITH first_seen AS (
            SELECT t.artist_id,
                   MIN(s.year * 100 + s.month) AS first_year_month,
                   MIN(s.year)                  AS first_year,
                   MIN(s.month)                 AS first_month
            FROM streams s JOIN tracks t ON s.track_id = t.track_id
            GROUP BY t.artist_id
        )
        SELECT first_year AS year, first_month AS month,
               first_year || '-' || PRINTF('%02d', first_month) AS year_month,
               COUNT(*) AS new_artists_discovered
        FROM first_seen GROUP BY first_year, first_month ORDER BY first_year, first_month
    """,
    "artist_loyalty": """
        WITH yearly_totals AS (
            SELECT a.artist_name, s.year,
                   ROUND(SUM(s.minutes_played), 1) AS total_minutes
            FROM streams s
            JOIN tracks t  ON s.track_id  = t.track_id
            JOIN artists a ON t.artist_id = a.artist_id
            GROUP BY a.artist_name, s.year
        ),
        ranked AS (
            SELECT yt.*,
                   (SELECT COUNT(*) FROM yearly_totals yt2
                    WHERE yt2.year = yt.year AND yt2.total_minutes > yt.total_minutes) + 1
                   AS rank_in_year
            FROM yearly_totals yt
        )
        SELECT artist_name,
               COUNT(DISTINCT year) AS years_in_top10,
               GROUP_CONCAT(year)   AS years_list
        FROM ranked WHERE rank_in_year <= 10
        GROUP BY artist_name HAVING years_in_top10 >= 3
        ORDER BY years_in_top10 DESC, artist_name
    """,
    "yearly_summary": """
        SELECT s.year,
               COUNT(*)                            AS total_plays,
               ROUND(SUM(s.minutes_played)/60, 1)  AS total_hours,
               COUNT(DISTINCT t.artist_id)          AS unique_artists,
               COUNT(DISTINCT s.track_id)           AS unique_tracks,
               ROUND(100.0*SUM(s.skipped)/COUNT(*),2) AS skip_rate_pct
        FROM streams s JOIN tracks t ON s.track_id = t.track_id
        GROUP BY s.year ORDER BY s.year
    """,
}


def main() -> None:
    log.info("=" * 55)
    log.info("  STEP 03 — ANALYSIS QUERIES")
    log.info("=" * 55)

    conn    = get_conn()
    results = {}

    for name, sql in QUERIES.items():
        try:
            results[name] = run_query(conn, name, sql)
        except Exception as e:
            log.error("Query failed [%s]: %s", name, e)

    conn.close()

    # ── Key insights ──────────────────────────────────────────────────────────
    log.info("KEY INSIGHTS")

    if "yearly_summary" in results:
        ys = results["yearly_summary"]
        log.info("Yearly listening summary:")
        for _, row in ys.iterrows():
            bar = "█" * int(row["total_hours"] / 100)
            log.info("  %d: %sh  %d artists  %s",
                     int(row["year"]), f"{row['total_hours']:>6.0f}",
                     int(row["unique_artists"]), bar)

    if "artist_loyalty" in results:
        loyal = results["artist_loyalty"]
        log.info("Most loyal artists (top-10 for 3+ years):")
        for _, row in loyal.head(5).iterrows():
            log.info("  %-30s → %d years", row["artist_name"], row["years_in_top10"])

    if "skip_rate_trend" in results:
        sr = results["skip_rate_trend"]
        log.info("Average skip rate: %.1f%%", sr["skip_rate_pct"].mean())
        log.info("Highest skip month: %s", sr.loc[sr["skip_rate_pct"].idxmax(), "year_month"])

    log.info("All reports saved to: %s", REPORTS_DIR)
    log.info("Next step → run: python scripts/04_diversity_index.py")


if __name__ == "__main__":
    main()
