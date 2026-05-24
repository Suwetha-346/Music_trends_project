"""
generate_synthetic_data.py
==========================
Generates realistic synthetic Spotify streaming history data (~150,000 records)
spanning 10 years (2015–2024). Models realistic behavior including:
  - Zipf's law for artist popularity
  - Seasonal listening patterns
  - Gradual genre/taste shifts over time
  - Platform evolution (mobile → desktop → smart speaker)
  - Realistic skip rates and session lengths

Run this FIRST before any other script.
"""

import sys
import os
import json
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import PATHS, PIPELINE
from logger import get_logger

log = get_logger(__name__)

random.seed(42)
np.random.seed(42)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Artist & Track Catalog
# ─────────────────────────────────────────────────────────────────────────────

# Artists grouped by "era" to model taste shifts
ARTIST_POOLS = {
    "pop_2015": [
        "Taylor Swift", "Ed Sheeran", "Ariana Grande", "Justin Bieber", "Katy Perry",
        "Selena Gomez", "Meghan Trainor", "Sam Smith", "One Direction", "Charlie Puth",
    ],
    "indie_2016": [
        "The 1975", "Arctic Monkeys", "Tame Impala", "Glass Animals", "Vampire Weekend",
        "Bon Iver", "Father John Misty", "Mac DeMarco", "Clairo", "Sufjan Stevens",
    ],
    "hiphop_2017": [
        "Kendrick Lamar", "Drake", "J. Cole", "Travis Scott", "Post Malone",
        "21 Savage", "Chance the Rapper", "Tyler, the Creator", "Frank Ocean", "SZA",
    ],
    "electronic_2018": [
        "Daft Punk", "Flume", "Odesza", "Kaytranada", "Four Tet",
        "Jon Hopkins", "Bonobo", "Aphex Twin", "Burial", "Nicolas Jaar",
    ],
    "rnb_2019": [
        "H.E.R.", "Daniel Caesar", "Brent Faiyaz", "Steve Lacy", "Lucky Daye",
        "Snoh Aalegra", "Jorja Smith", "Kiana Ledé", "Ari Lennox", "Summer Walker",
    ],
    "rock_2020": [
        "Radiohead", "The National", "Phoebe Bridgers", "Big Thief", "Soccer Mommy",
        "Japanese Breakfast", "Lucy Dacus", "Waxahatchee", "Mitski", "Adrianne Lenker",
    ],
    "kpop_2021": [
        "BTS", "BLACKPINK", "EXO", "TWICE", "Stray Kids",
        "aespa", "IVE", "NewJeans", "Le Sserafim", "Red Velvet",
    ],
    "pop_2022": [
        "Harry Styles", "Olivia Rodrigo", "Doja Cat", "Dua Lipa", "The Weeknd",
        "Billie Eilish", "Lana Del Rey", "SZA", "Gracie Abrams", "Sabrina Carpenter",
    ],
    "metal_2023": [
        "Metallica", "Bring Me the Horizon", "Spiritbox", "Knocked Loose", "Muse",
        "Architects", "Paramore", "My Chemical Romance", "Pierce the Veil", "Polyphia",
    ],
    "ambient_2024": [
        "Brian Eno", "Max Richter", "Nils Frahm", "William Basinski", "Grouper",
        "Stars of the Lid", "Tim Hecker", "Hammock", "Caspian", "Godspeed You! Black Emperor",
    ],
    "timeless": [  # Artists present throughout
        "The Beatles", "David Bowie", "Queen", "Fleetwood Mac", "Pink Floyd",
        "Led Zeppelin", "Bob Dylan", "The Rolling Stones", "Michael Jackson", "Prince",
    ],
}

# Flatten all artists
ALL_ARTISTS = []
for pool in ARTIST_POOLS.values():
    ALL_ARTISTS.extend(pool)

# Generate track catalog: 5-10 tracks per artist
def make_tracks_for_artist(artist):
    n = random.randint(5, 12)
    tracks = []
    adjectives = ["Blue", "Golden", "Midnight", "Electric", "Silent", "Falling", "Rising",
                  "Broken", "Wild", "Lost", "Neon", "Dark", "Bright", "Cold", "Warm"]
    nouns = ["Heart", "Road", "Night", "Dream", "Sky", "Rain", "Fire", "Soul", "Eyes",
             "Light", "Stars", "Waves", "Shadows", "Love", "Years"]
    albums = [f"{random.choice(adjectives)} {random.choice(nouns)}" for _ in range(3)]
    for _ in range(n):
        name = f"{random.choice(adjectives)} {random.choice(nouns)}"
        tracks.append({
            "artist": artist,
            "track": name,
            "album": random.choice(albums),
            "duration_ms": random.randint(150_000, 360_000),
            "uri": f"spotify:track:{abs(hash(artist + name)) % 10**22:022d}",
        })
    return tracks

TRACK_CATALOG = []
for artist in ALL_ARTISTS:
    TRACK_CATALOG.extend(make_tracks_for_artist(artist))

TRACK_DF = pd.DataFrame(TRACK_CATALOG)

# ─────────────────────────────────────────────────────────────────────────────
# 2. Simulation Parameters
# ─────────────────────────────────────────────────────────────────────────────

START_DATE  = datetime(2015, 1, 1)
END_DATE    = datetime(2024, 12, 31)
TARGET_ROWS = PIPELINE["target_records"]

PLATFORMS = ["Android", "iOS", "Windows", "macOS", "Cast to device", "Web Player"]
PLATFORM_WEIGHTS_BY_YEAR = {
    2015: [0.40, 0.35, 0.15, 0.05, 0.02, 0.03],
    2016: [0.38, 0.35, 0.14, 0.06, 0.03, 0.04],
    2017: [0.35, 0.33, 0.14, 0.08, 0.05, 0.05],
    2018: [0.30, 0.30, 0.15, 0.12, 0.07, 0.06],
    2019: [0.28, 0.28, 0.15, 0.14, 0.09, 0.06],
    2020: [0.25, 0.25, 0.20, 0.18, 0.05, 0.07],  # COVID → desktop ↑
    2021: [0.27, 0.27, 0.18, 0.16, 0.05, 0.07],
    2022: [0.30, 0.28, 0.16, 0.14, 0.06, 0.06],
    2023: [0.32, 0.30, 0.14, 0.12, 0.06, 0.06],
    2024: [0.33, 0.31, 0.13, 0.11, 0.06, 0.06],
}

COUNTRIES = ["US", "GB", "CA", "AU", "IN", "DE", "FR", "BR", "JP", "MX"]
COUNTRY_WEIGHTS = [0.45, 0.15, 0.10, 0.07, 0.05, 0.04, 0.04, 0.04, 0.03, 0.03]

REASON_STARTS = ["trackdone", "clickrow", "fwdbtn", "backbtn", "playbtn", "remote", "appload"]
REASON_ENDS   = ["trackdone", "fwdbtn", "endplay", "logout", "backbtn", "remote", "unexpected-exit"]

# ─────────────────────────────────────────────────────────────────────────────
# 3. Artist weight by year (taste evolution)
# ─────────────────────────────────────────────────────────────────────────────

def get_artist_weights(year: int) -> np.ndarray:
    """
    Returns sampling probability for each artist given the year.
    Models gradual taste shifts: earlier eras fade, newer eras rise.
    Timeless artists always have base weight.
    """
    weights = np.zeros(len(ALL_ARTISTS))
    for i, artist in enumerate(ALL_ARTISTS):
        # Find which pool this artist belongs to
        base_w = 0.0
        for pool_name, pool_artists in ARTIST_POOLS.items():
            if artist in pool_artists:
                if pool_name == "timeless":
                    base_w += 0.8  # always present
                else:
                    # Extract the "peak" year from pool name
                    peak_year = int(pool_name.split("_")[-1])
                    distance = abs(year - peak_year)
                    # Gaussian decay around peak year
                    base_w += np.exp(-0.5 * (distance / 2.0) ** 2) * 2.0
        weights[i] = max(base_w, 0.01)

    # Apply Zipf-like skew: sort by weight, apply power law
    rank_order = np.argsort(-weights)
    zipf_weights = np.zeros(len(ALL_ARTISTS))
    for rank, idx in enumerate(rank_order):
        zipf_weights[idx] = weights[idx] / ((rank + 1) ** 0.4)

    return zipf_weights / zipf_weights.sum()


# ─────────────────────────────────────────────────────────────────────────────
# 4. Session generation
# ─────────────────────────────────────────────────────────────────────────────

def get_hourly_weight(hour: int, month: int) -> float:
    """Models listening intensity by hour and season."""
    # Peak hours: commute (8-9), lunch (12-13), evening (18-22)
    hour_w = np.array([
        0.2, 0.1, 0.1, 0.1, 0.2, 0.4, 0.7, 1.0,  # 0-7
        1.2, 1.1, 0.9, 0.9, 1.1, 1.0, 0.8, 0.7,   # 8-15
        0.8, 0.9, 1.3, 1.5, 1.5, 1.3, 1.0, 0.6,   # 16-23
    ])
    # Winter months: more listening overall
    season_w = 1.0 + 0.2 * np.cos(np.pi * (month - 1) / 6)
    return float(hour_w[hour] * season_w)


def generate_stream_record(dt: datetime, year: int, artist_weights: np.ndarray) -> dict:
    """Generate a single stream record."""
    # Sample artist
    artist_idx = np.random.choice(len(ALL_ARTISTS), p=artist_weights)
    artist = ALL_ARTISTS[artist_idx]

    # Sample a track from this artist
    artist_tracks = TRACK_DF[TRACK_DF["artist"] == artist]
    if len(artist_tracks) == 0:
        artist_tracks = TRACK_DF.sample(1)
    track_row = artist_tracks.sample(1).iloc[0]

    # Determine if skipped (skip rate decreases for familiar artists)
    skipped = random.random() < 0.25

    if skipped:
        ms_played = random.randint(5_000, 28_000)
    else:
        # Play 60–100% of track
        pct = random.uniform(0.6, 1.0)
        ms_played = int(track_row["duration_ms"] * pct)

    platform_w = PLATFORM_WEIGHTS_BY_YEAR.get(year, PLATFORM_WEIGHTS_BY_YEAR[2024])
    platform = random.choices(PLATFORMS, weights=platform_w, k=1)[0]

    return {
        "ts": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "master_metadata_track_artist_name": artist,
        "master_metadata_track_name": track_row["track"],
        "master_metadata_album_album_name": track_row["album"],
        "spotify_track_uri": track_row["uri"],
        "ms_played": ms_played,
        "platform": platform,
        "conn_country": random.choices(COUNTRIES, weights=COUNTRY_WEIGHTS, k=1)[0],
        "reason_start": random.choice(REASON_STARTS),
        "reason_end": random.choice(REASON_ENDS),
        "shuffle": random.random() < 0.4,
        "skipped": skipped,
        "username": "spotify_user_demo",
        "ip_addr_decrypted": f"192.168.{random.randint(0,255)}.{random.randint(1,254)}",
        "user_agent_decrypted": "unknown",
        "episode_name": None,
        "episode_show_name": None,
        "spotify_episode_uri": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. Main generation loop
# ─────────────────────────────────────────────────────────────────────────────

def generate_all_records() -> list[dict]:
    total_days = (END_DATE - START_DATE).days + 1

    # Pre-compute artist weights per year
    yearly_weights = {yr: get_artist_weights(yr) for yr in range(2015, 2025)}

    # Estimate streams per day (varies by year + COVID spike in 2020)
    streams_per_day_base = TARGET_ROWS / total_days
    year_multipliers = {
        2015: 0.7, 2016: 0.8, 2017: 0.9, 2018: 1.0, 2019: 1.1,
        2020: 1.4,  # COVID lockdown → massive spike
        2021: 1.2, 2022: 1.1, 2023: 1.0, 2024: 1.0,
    }

    records = []
    current_date = START_DATE
    log.info("Generating synthetic Spotify data (%s target records)", f"{TARGET_ROWS:,}")

    while current_date <= END_DATE:
        year = current_date.year
        month = current_date.month
        weekday = current_date.weekday()  # 0=Mon, 6=Sun
        is_weekend = weekday >= 5

        # More listening on weekends
        weekend_boost = 1.3 if is_weekend else 1.0
        n_streams = int(np.random.poisson(
            streams_per_day_base * year_multipliers[year] * weekend_boost
        ))

        artist_weights = yearly_weights[year]

        # Generate streams for this day across realistic hours
        for _ in range(n_streams):
            # Sample hour weighted by time-of-day pattern
            hour_weights = np.array([get_hourly_weight(h, month) for h in range(24)])
            hour_weights /= hour_weights.sum()
            hour = np.random.choice(24, p=hour_weights)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)

            dt = current_date.replace(hour=hour, minute=minute, second=second)
            records.append(generate_stream_record(dt, year, artist_weights))

        current_date += timedelta(days=1)

        if len(records) % 10_000 == 0 and len(records) > 0:
            log.info("  Generated %s records... (%s)", f"{len(records):,}", current_date.date())

    log.info("Generated %s total records", f"{len(records):,}")
    return records


# ─────────────────────────────────────────────────────────────────────────────
# 6. Save to JSON files (mimics real Spotify export format)
# ─────────────────────────────────────────────────────────────────────────────

def save_as_json_chunks(records: list[dict], output_dir: str, chunk_size: int = 40_000):
    os.makedirs(output_dir, exist_ok=True)
    chunks = [records[i:i+chunk_size] for i in range(0, len(records), chunk_size)]
    for i, chunk in enumerate(chunks):
        fname = os.path.join(output_dir, f"Streaming_History_Audio_2015-2024_{i}.json")
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)
        log.info("  Saved: %s (%s records)", os.path.basename(fname), f"{len(chunk):,}")


if __name__ == "__main__":
    records    = generate_all_records()
    output_dir = PATHS["raw_data"]
    log.info("Saving to %s...", output_dir)
    save_as_json_chunks(records, output_dir)
    log.info("Synthetic data generation complete!")
    log.info("Next step → run: python scripts/01_data_cleaning.py")
