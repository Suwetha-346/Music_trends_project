"""
01_data_cleaning.py
===================
ETL Script — Extract, Transform, Load (to CSV)

Reads all Spotify Extended Streaming History JSON files from data/raw/,
cleans and transforms them into a single analysis-ready CSV.

Run after: generate_synthetic_data.py
Run before: 02_load_to_db.py
"""

import os
import glob
import json
import sys

import pandas as pd
import numpy as np

# ─── Project imports ──────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PATHS, PIPELINE
from logger import get_logger

log = get_logger(__name__)

RAW_DIR    = PATHS["raw_data"]
OUTPUT_CSV = PATHS["cleaned_csv"]
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)


# ─── Step 1: Load all JSON files ──────────────────────────────────────────────
def load_raw_data(raw_dir: str) -> pd.DataFrame:
    json_files = sorted(glob.glob(os.path.join(raw_dir, "Streaming_History_Audio_*.json")))
    if not json_files:
        raise FileNotFoundError(
            f"No Streaming_History_Audio_*.json files found in {raw_dir}\n"
            "Run generate_synthetic_data.py first."
        )

    log.info("Found %d JSON file(s):", len(json_files))
    frames = []
    for fpath in json_files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        log.info("  %s → %s rows", os.path.basename(fpath), f"{len(df):,}")
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    log.info("Total raw records loaded: %s", f"{combined.shape[0]:,}")
    return combined


# ─── Step 2: Filter out podcasts & junk ───────────────────────────────────────
def filter_music_only(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df[df["spotify_track_uri"].notna()].copy()
    df = df[df["episode_name"].isna()].copy()
    after = len(df)
    log.info("Dropped %s podcast/episode rows → %s music rows remain",
             f"{before - after:,}", f"{after:,}")
    return df


# ─── Step 3: Filter short plays (skips < 30 seconds) ─────────────────────────
def filter_short_plays(df: pd.DataFrame) -> pd.DataFrame:
    min_ms = PIPELINE["min_ms_played"]
    before = len(df)
    df = df[df["ms_played"] >= min_ms].copy()
    after = len(df)
    log.info("Dropped %s plays < %ds → %s rows remain",
             f"{before - after:,}", min_ms // 1000, f"{after:,}")
    return df


# ─── Step 4: Standardize & clean text fields ──────────────────────────────────
def clean_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    text_cols = [
        "master_metadata_track_artist_name",
        "master_metadata_track_name",
        "master_metadata_album_album_name",
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.replace(r"\s+", " ", regex=True)
                .replace("nan", pd.NA)
            )

    before = len(df)
    df = df.dropna(subset=["master_metadata_track_artist_name", "master_metadata_track_name"])
    after = len(df)
    if before != after:
        log.warning("Dropped %s rows with missing artist/track name", f"{before - after:,}")

    log.info("Text fields standardized")
    return df


# ─── Step 5: Drop PII columns ─────────────────────────────────────────────────
def drop_pii_columns(df: pd.DataFrame) -> pd.DataFrame:
    pii_cols = ["ip_addr_decrypted", "user_agent_decrypted", "username",
                "episode_name", "episode_show_name", "spotify_episode_uri"]
    cols_to_drop = [c for c in pii_cols if c in df.columns]
    df = df.drop(columns=cols_to_drop)
    log.info("Dropped %d PII/irrelevant columns", len(cols_to_drop))
    return df


# ─── Step 6: Feature engineering ──────────────────────────────────────────────
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df["played_at"] = pd.to_datetime(df["ts"], utc=True).dt.tz_localize(None)
    df["year"]        = df["played_at"].dt.year
    df["month"]       = df["played_at"].dt.month
    df["day_of_week"] = df["played_at"].dt.dayofweek   # 0=Mon, 6=Sun
    df["hour"]        = df["played_at"].dt.hour
    df["date"]        = df["played_at"].dt.date
    df["year_month"]  = df["played_at"].dt.to_period("M").astype(str)
    df["minutes_played"] = (df["ms_played"] / 60_000).round(4)

    for col in ["shuffle", "skipped"]:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)

    log.info("Feature engineering complete (year, month, hour, minutes_played, year_month)")
    return df


# ─── Step 7: Rename & select final columns ────────────────────────────────────
def select_final_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "master_metadata_track_artist_name": "artist_name",
        "master_metadata_track_name":        "track_name",
        "master_metadata_album_album_name":  "album_name",
        "spotify_track_uri":                 "spotify_uri",
        "conn_country":                      "country",
    }
    df = df.rename(columns=rename_map)

    final_cols = [
        "played_at", "year", "month", "day_of_week", "hour", "date", "year_month",
        "artist_name", "track_name", "album_name", "spotify_uri",
        "ms_played", "minutes_played",
        "platform", "country", "reason_start", "reason_end", "shuffle", "skipped",
    ]
    existing = [c for c in final_cols if c in df.columns]
    df = df[existing].sort_values("played_at").reset_index(drop=True)
    log.info("Final columns selected: %s", list(df.columns))
    return df


# ─── Step 8: Print summary statistics ─────────────────────────────────────────
def log_summary(df: pd.DataFrame) -> None:
    log.info("=" * 55)
    log.info("  DATA CLEANING SUMMARY")
    log.info("=" * 55)
    log.info("  Total records:      %s", f"{len(df):>10,}")
    log.info("  Date range:         %s → %s",
             df["played_at"].min().date(), df["played_at"].max().date())
    log.info("  Years covered:      %d – %d", df["year"].min(), df["year"].max())
    log.info("  Unique artists:     %s", f"{df['artist_name'].nunique():>10,}")
    log.info("  Unique tracks:      %s", f"{df['track_name'].nunique():>10,}")
    log.info("  Total hours played: %s hrs", f"{df['minutes_played'].sum() / 60:>10,.1f}")
    log.info("  Skip rate:          %s%%", f"{df['skipped'].mean() * 100:>9.1f}")

    log.info("  Records per year:")
    year_counts = df.groupby("year").agg(
        plays=("played_at", "count"),
        hours=("minutes_played", lambda x: x.sum() / 60)
    )
    for yr, row in year_counts.iterrows():
        bar = "█" * int(row["plays"] / 500)
        log.info("    %d: %s plays  %sh  %s",
                 yr, f"{row['plays']:>6,}", f"{row['hours']:>6.0f}", bar)


# ─── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    log.info("=" * 55)
    log.info("  STEP 01 — DATA CLEANING")
    log.info("=" * 55)

    df = load_raw_data(RAW_DIR)
    df = filter_music_only(df)
    df = filter_short_plays(df)
    df = clean_text_fields(df)
    df = drop_pii_columns(df)
    df = engineer_features(df)
    df = select_final_columns(df)

    log_summary(df)

    df.to_csv(OUTPUT_CSV, index=False)
    log.info("Saved cleaned data → %s", OUTPUT_CSV)
    log.info("Next step → run: python scripts/02_load_to_db.py")


if __name__ == "__main__":
    main()
