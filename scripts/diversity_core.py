"""
scripts/diversity_core.py
=========================
Pure-function library for diversity metric calculations.

Extracted from 04_diversity_index.py so that:
  - Unit tests can import functions without side-effects (no DB calls, no I/O)
  - The main script stays thin (orchestration only)

Functions
---------
shannon_entropy(series)         → float
evenness(H, n_unique)           → float
compute_monthly_metrics(df)     → pd.DataFrame
add_rolling_averages(df, win)   → pd.DataFrame
detect_change_points(df, thr)   → pd.DataFrame
"""

import numpy as np
import pandas as pd


def shannon_entropy(series: pd.Series) -> float:
    """
    Compute Shannon Entropy H for a categorical series of artist plays.

    H = -Σ p_i * ln(p_i)

    Parameters
    ----------
    series : pd.Series
        Each element is one play's artist name.

    Returns
    -------
    float
        Shannon Entropy (nats). Returns 0.0 for a single-category series.
    """
    counts = series.value_counts()
    props = counts / counts.sum()
    props = props[props > 0]          # guard against log(0)
    return float(-np.sum(props * np.log(props)))


def evenness(H: float, n_unique: int) -> float:
    """
    Pielou's Evenness: E = H / ln(n), normalised to [0, 1].

    Returns 0.0 when n_unique <= 1 (avoids division by zero / log(0)).
    """
    if n_unique <= 1:
        return 0.0
    return float(H / np.log(n_unique))


def compute_monthly_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-month diversity metrics from a streams DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns: year, month, artist_name.

    Returns
    -------
    pd.DataFrame
        One row per (year, month) with columns:
        year, month, year_month, total_plays, unique_artists, new_artists,
        shannon_entropy, normalized_entropy, new_artist_ratio, top1_concentration.
    """
    # ── Vectorized first-seen map (replaces slow iterrows loop) ───────────────
    # Find the minimum year*100+month for each artist in one groupby pass.
    df = df.sort_values(["year", "month"]).reset_index(drop=True)
    df["ym_int"] = df["year"] * 100 + df["month"]
    first_seen_ym = (
        df.groupby("artist_name")["ym_int"].min().rename("first_ym")
    )
    df = df.join(first_seen_ym, on="artist_name")

    records = []
    for (year, month), group in df.groupby(["year", "month"]):
        year, month = int(year), int(month)
        ym_int = year * 100 + month
        artists = group["artist_name"]
        total_plays    = len(artists)
        unique_artists = artists.nunique()

        H = shannon_entropy(artists)
        E = evenness(H, unique_artists)

        # New artists: those whose first_ym equals this month
        new_artists = int((group["first_ym"] == ym_int).sum())
        new_artist_ratio = new_artists / unique_artists if unique_artists > 0 else 0.0

        top1_plays = artists.value_counts().iloc[0]
        top1_concentration = top1_plays / total_plays if total_plays > 0 else 0.0

        records.append({
            "year":               year,
            "month":              month,
            "year_month":         f"{year}-{month:02d}",
            "total_plays":        total_plays,
            "unique_artists":     unique_artists,
            "new_artists":        new_artists,
            "shannon_entropy":    round(H, 6),
            "normalized_entropy": round(E, 6),
            "new_artist_ratio":   round(new_artist_ratio, 6),
            "top1_concentration": round(top1_concentration, 6),
        })

    return pd.DataFrame(records).sort_values(["year", "month"]).reset_index(drop=True)


def add_rolling_averages(metrics: pd.DataFrame, window: int = 3) -> pd.DataFrame:
    """Add centred rolling averages for the four core metrics."""
    for col in ["shannon_entropy", "normalized_entropy",
                "new_artist_ratio", "top1_concentration"]:
        metrics[f"{col}_rolling{window}"] = (
            metrics[col]
            .rolling(window=window, center=True, min_periods=1)
            .mean()
            .round(6)
        )
    return metrics


def detect_change_points(
    metrics: pd.DataFrame, threshold_std: float = 1.5
) -> pd.DataFrame:
    """
    Flag months where the absolute change in Shannon Entropy exceeds
    μ + threshold_std * σ of all month-over-month deltas.

    Adds columns: entropy_delta (float), is_change_point (0/1 int).
    """
    delta = metrics["shannon_entropy"].diff().abs()
    mean, std = delta.mean(), delta.std()
    metrics = metrics.copy()
    metrics["entropy_delta"]   = delta.round(6)
    metrics["is_change_point"] = (delta > mean + threshold_std * std).astype(int)
    return metrics
