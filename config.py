"""
config.py
=========
Central configuration for the Spotify Music Evolution project.

All pipeline scripts import from here — no more hardcoded paths or
scattered constants. To adapt this project to a new machine or MySQL
instance, only this file needs to change.

Usage:
    from config import PATHS, DB, PIPELINE
"""

import os

# ─── Root directory (project root, not this file's dir) ──────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Path registry ────────────────────────────────────────────────────────────
PATHS = {
    "base":         BASE_DIR,
    "raw_data":     os.path.join(BASE_DIR, "data", "raw"),
    "cleaned_csv":  os.path.join(BASE_DIR, "data", "cleaned_streaming.csv"),
    "db":           os.path.join(BASE_DIR, "data", "spotify_evolution.db"),
    "reports":      os.path.join(BASE_DIR, "output", "reports"),
    "charts":       os.path.join(BASE_DIR, "output", "charts"),
    "logs":         os.path.join(BASE_DIR, "output", "logs"),
    "scripts":      os.path.join(BASE_DIR, "scripts"),
}

# ─── Database ─────────────────────────────────────────────────────────────────
DB = {
    # Set USE_MYSQL=True and fill credentials below to use MySQL instead of SQLite
    "use_mysql":    False,
    "host":         "localhost",
    "port":         3306,
    "user":         "root",
    "password":     os.environ.get("SPOTIFY_DB_PASSWORD", "your_password_here"),
    "name":         "spotify_evolution",
}

# ─── Pipeline defaults ────────────────────────────────────────────────────────
PIPELINE = {
    # Minimum ms played to count as a real listen (not a skip)
    "min_ms_played":            30_000,

    # Rolling-average window for diversity metrics (months)
    "diversity_rolling_window": 3,

    # Std-deviation multiplier for change-point detection
    "change_point_threshold":   1.5,

    # Batch size for stream inserts
    "db_batch_size":            5_000,

    # Target records for synthetic data generation
    "target_records":           155_000,
}
