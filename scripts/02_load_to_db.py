"""
02_load_to_db.py
================
Loads the cleaned CSV into SQLite (default) or MySQL.
SQLite = zero setup, single file. Set DB["use_mysql"] = True in config.py for MySQL.

Run after: 01_data_cleaning.py
Run before: 03_analysis_queries.py
"""

import os
import sqlite3
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PATHS, DB as DB_CFG, PIPELINE
from logger import get_logger

log = get_logger(__name__)

CSV_PATH = PATHS["cleaned_csv"]
DB_PATH  = PATHS["db"]

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS artists (
    artist_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS tracks (
    track_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    track_name  TEXT NOT NULL,
    album_name  TEXT,
    artist_id   INTEGER NOT NULL,
    spotify_uri TEXT,
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
);
CREATE TABLE IF NOT EXISTS streams (
    stream_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id       INTEGER NOT NULL,
    played_at      TEXT NOT NULL,
    ms_played      INTEGER NOT NULL,
    minutes_played REAL NOT NULL,
    platform       TEXT,
    country        TEXT,
    reason_start   TEXT,
    reason_end     TEXT,
    shuffle        INTEGER DEFAULT 0,
    skipped        INTEGER DEFAULT 0,
    year           INTEGER NOT NULL,
    month          INTEGER NOT NULL,
    day_of_week    INTEGER NOT NULL,
    hour           INTEGER NOT NULL,
    FOREIGN KEY (track_id) REFERENCES tracks(track_id)
);
CREATE TABLE IF NOT EXISTS diversity_metrics (
    metric_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    year               INTEGER NOT NULL,
    month              INTEGER NOT NULL,
    total_plays        INTEGER NOT NULL,
    unique_artists     INTEGER NOT NULL,
    shannon_entropy    REAL NOT NULL,
    normalized_entropy REAL NOT NULL,
    new_artist_ratio   REAL NOT NULL,
    top1_concentration REAL NOT NULL,
    UNIQUE (year, month)
);
CREATE INDEX IF NOT EXISTS idx_streams_year       ON streams(year);
CREATE INDEX IF NOT EXISTS idx_streams_year_month ON streams(year, month);
CREATE INDEX IF NOT EXISTS idx_streams_played_at  ON streams(played_at);
CREATE INDEX IF NOT EXISTS idx_tracks_artist      ON tracks(artist_id);
"""


def get_connection():
    if DB_CFG["use_mysql"]:
        from sqlalchemy import create_engine
        cfg = DB_CFG
        url = (f"mysql+pymysql://{cfg['user']}:{cfg['password']}"
               f"@{cfg['host']}:{cfg['port']}/{cfg['name']}?charset=utf8mb4")
        engine = create_engine(url, pool_pre_ping=True)
        log.info("Connected to MySQL: %s/%s", cfg["host"], cfg["name"])
        return engine, "mysql"
    else:
        conn = sqlite3.connect(DB_PATH)
        log.info("Connected to SQLite: %s", DB_PATH)
        return conn, "sqlite"


def create_schema(conn, db_type: str) -> None:
    if db_type == "sqlite":
        cursor = conn.cursor()
        for stmt in SQLITE_SCHEMA.strip().split(";"):
            s = stmt.strip()
            if s:
                cursor.execute(s)
        conn.commit()
        log.info("SQLite schema created")


def load_csv() -> pd.DataFrame:
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Run 01_data_cleaning.py first. Missing: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH, parse_dates=["played_at"])
    log.info("Loaded %s rows from cleaned CSV", f"{len(df):,}")
    return df


def insert_artists(df: pd.DataFrame, conn, db_type: str) -> dict:
    unique_artists = df["artist_name"].dropna().unique().tolist()
    cursor = conn.cursor()
    for name in unique_artists:
        cursor.execute("INSERT OR IGNORE INTO artists (artist_name) VALUES (?)", (name,))
    conn.commit()
    cursor.execute("SELECT artist_id, artist_name FROM artists")
    artist_map = {row[1]: row[0] for row in cursor.fetchall()}
    log.info("Inserted %s artists", f"{len(artist_map):,}")
    return artist_map


def insert_tracks(df: pd.DataFrame, conn, db_type: str, artist_map: dict) -> dict:
    tracks_df = df[["track_name", "album_name", "artist_name", "spotify_uri"]].drop_duplicates(
        subset=["track_name", "artist_name"]
    ).copy()
    tracks_df["artist_id"] = tracks_df["artist_name"].map(artist_map)
    cursor = conn.cursor()
    for _, row in tracks_df.iterrows():
        cursor.execute(
            "INSERT OR IGNORE INTO tracks (track_name, album_name, artist_id, spotify_uri) VALUES (?,?,?,?)",
            (row["track_name"], row.get("album_name"), int(row["artist_id"]), row.get("spotify_uri"))
        )
    conn.commit()
    cursor.execute("SELECT track_id, track_name, artist_id FROM tracks")
    track_map = {(row[1], row[2]): row[0] for row in cursor.fetchall()}
    log.info("Inserted %s tracks", f"{len(track_map):,}")
    return track_map


def insert_streams(df: pd.DataFrame, conn, db_type: str,
                   artist_map: dict, track_map: dict) -> None:
    batch_size = PIPELINE["db_batch_size"]
    df = df.copy()
    df["artist_id"] = df["artist_name"].map(artist_map)
    df["track_id"]  = df.apply(lambda r: track_map.get((r["track_name"], r["artist_id"])), axis=1)
    df = df.dropna(subset=["track_id"])
    df["track_id"]  = df["track_id"].astype(int)
    df["played_at"] = df["played_at"].astype(str)
    df["shuffle"]   = df["shuffle"].astype(int)
    df["skipped"]   = df["skipped"].astype(int)

    cols = ["track_id", "played_at", "ms_played", "minutes_played", "platform", "country",
            "reason_start", "reason_end", "shuffle", "skipped", "year", "month", "day_of_week", "hour"]
    records = df[cols].to_records(index=False).tolist()
    cursor  = conn.cursor()
    total   = len(records)

    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]
        cursor.executemany(
            "INSERT INTO streams (track_id,played_at,ms_played,minutes_played,platform,country,"
            "reason_start,reason_end,shuffle,skipped,year,month,day_of_week,hour) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            batch
        )
        conn.commit()
        log.info("Streams: %s/%s", f"{min(i + batch_size, total):,}", f"{total:,}")

    log.info("Inserted %s stream records", f"{total:,}")


def verify_counts(conn, db_type: str) -> None:
    cursor = conn.cursor()
    for table in ["artists", "tracks", "streams"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        log.info("  %-12s → %s rows", table, f"{cursor.fetchone()[0]:>8,}")


def main() -> None:
    log.info("=" * 55)
    log.info("  STEP 02 — LOAD TO DATABASE")
    log.info("=" * 55)
    conn, db_type = get_connection()
    create_schema(conn, db_type)
    df = load_csv()
    artist_map = insert_artists(df, conn, db_type)
    track_map  = insert_tracks(df, conn, db_type, artist_map)
    insert_streams(df, conn, db_type, artist_map, track_map)
    log.info("Row counts:")
    verify_counts(conn, db_type)
    if db_type == "sqlite":
        conn.close()
    log.info("Database saved → %s", DB_PATH)
    log.info("Next step → run: python scripts/03_analysis_queries.py")


if __name__ == "__main__":
    main()
