"""
05_visualizations.py
====================
Generates 10 Matplotlib charts (dark theme) from analysis outputs.

Run after: 03_analysis_queries.py AND 04_diversity_index.py
"""

import os
import sys
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PATHS
from logger import get_logger

log = get_logger(__name__)

REPORTS_DIR = PATHS["reports"]
CHARTS_DIR  = PATHS["charts"]
os.makedirs(CHARTS_DIR, exist_ok=True)

# ── Dark theme ────────────────────────────────────────────────────────────────
DARK_BG   = "#0d0f14"
CARD_BG   = "#141720"
GRID_CLR  = "#1e2130"
TEXT_CLR  = "#e8eaf0"
MUTED_CLR = "#6b7280"
PALETTE   = ["#6c63ff", "#ff6584", "#43d9ad", "#f9a825", "#29b6f6",
             "#ef5350", "#ab47bc", "#66bb6a", "#ff7043", "#26c6da"]

plt.rcParams.update({
    "figure.facecolor": DARK_BG,  "axes.facecolor":  CARD_BG,
    "axes.edgecolor":   GRID_CLR, "axes.labelcolor": TEXT_CLR,
    "axes.titlecolor":  TEXT_CLR, "xtick.color":     MUTED_CLR,
    "ytick.color":      MUTED_CLR,"text.color":      TEXT_CLR,
    "grid.color":       GRID_CLR, "grid.linewidth":  0.5,
    "font.family":      "DejaVu Sans",
    "axes.titlesize":   13,       "axes.labelsize":  10,
    "figure.dpi":       120,
})


def save(fig, name: str) -> None:
    path = os.path.join(CHARTS_DIR, name)
    fig.savefig(path, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    log.info("Saved: %s", name)


def load_csv(name: str) -> pd.DataFrame:
    path = os.path.join(REPORTS_DIR, f"{name}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {path}. Run 03/04 scripts first.")
    return pd.read_csv(path)


# ── Chart 1: Monthly Listening Hours ─────────────────────────────────────────
def chart_listening_timeline() -> None:
    df = load_csv("monthly_listening_hours")
    fig, ax = plt.subplots(figsize=(16, 5))
    x = range(len(df))
    ax.fill_between(x, df["total_hours"], alpha=0.25, color=PALETTE[0])
    ax.plot(x, df["total_hours"], color=PALETTE[0], linewidth=1.8)
    for yr in range(2016, 2025):
        idx = df[df["year"] == yr].index
        if len(idx):
            ax.axvline(idx[0] - df.index[0], color=GRID_CLR, linewidth=1, linestyle="--", alpha=0.7)
            ax.text(idx[0] - df.index[0] + 0.5, ax.get_ylim()[1] * 0.92,
                    str(yr), color=MUTED_CLR, fontsize=8)
    ax.set_title("🎵 Monthly Listening Hours — 10-Year Timeline", fontsize=15, pad=14)
    ax.set_xlabel("Month"); ax.set_ylabel("Hours Listened")
    ax.set_xticks(list(x)[::6])
    ax.set_xticklabels(df["year_month"].iloc[::6], rotation=45, ha="right", fontsize=7)
    ax.grid(axis="y", alpha=0.4); ax.set_xlim(0, len(df) - 1)
    save(fig, "01_listening_timeline.png")


# ── Chart 2: Diversity Index Over Time ───────────────────────────────────────
def chart_diversity_index() -> None:
    df = load_csv("diversity_metrics")
    if "year_month" not in df.columns:
        df["year_month"] = df["year"].astype(str) + "-" + df["month"].apply(lambda m: f"{int(m):02d}")
    fig, ax = plt.subplots(figsize=(16, 5))
    x = range(len(df))
    col = "shannon_entropy_rolling3" if "shannon_entropy_rolling3" in df.columns else "shannon_entropy"
    ax.fill_between(x, df[col], alpha=0.2, color=PALETTE[2])
    ax.plot(x, df[col], color=PALETTE[2], linewidth=2, label="Diversity Index (H)")
    ax.plot(x, df["shannon_entropy"], color=PALETTE[2], linewidth=0.6, alpha=0.35)
    if "is_change_point" in df.columns:
        for idx_val, row in df[df["is_change_point"] == 1].iterrows():
            pos = df.index.get_loc(idx_val)
            ax.axvline(pos, color=PALETTE[1], linewidth=1.2, linestyle=":", alpha=0.85)
            ax.text(pos + 0.3, df[col].max() * 0.96,
                    row["year_month"], color=PALETTE[1], fontsize=6.5, rotation=90)
    ax.set_title("📈 Music Diversity Index Over Time  (Shannon Entropy)", fontsize=15, pad=14)
    ax.set_xlabel("Month"); ax.set_ylabel("Shannon Entropy (H)")
    ax.set_xticks(list(x)[::6])
    ax.set_xticklabels(df["year_month"].iloc[::6], rotation=45, ha="right", fontsize=7)
    ax.grid(axis="y", alpha=0.4)
    ax.legend(handles=[
        mpatches.Patch(color=PALETTE[2], label="Diversity Index (3-mo avg)"),
        mpatches.Patch(color=PALETTE[1], label="Change Point"),
    ], loc="lower right", facecolor=CARD_BG, edgecolor=GRID_CLR)
    save(fig, "02_diversity_index.png")


# ── Chart 3: Top Artists Heatmap ─────────────────────────────────────────────
def chart_top_artists_heatmap() -> None:
    df = load_csv("top_artists_by_year")
    years = sorted(df["year"].unique())
    top_artists = df.groupby("artist_name")["total_minutes"].sum().nlargest(15).index.tolist()
    pivot = df[df["artist_name"].isin(top_artists)].pivot_table(
        index="artist_name", columns="year", values="total_minutes",
        aggfunc="sum", fill_value=0
    ).reindex(columns=years, fill_value=0)
    cmap = LinearSegmentedColormap.from_list("sp", ["#141720", "#6c63ff", "#ff6584"])
    fig, ax = plt.subplots(figsize=(14, 8))
    im = ax.imshow(pivot.values, aspect="auto", cmap=cmap, interpolation="nearest")
    ax.set_xticks(range(len(years))); ax.set_xticklabels(years, fontsize=9)
    ax.set_yticks(range(len(pivot.index))); ax.set_yticklabels(pivot.index, fontsize=9)
    for i in range(len(pivot.index)):
        for j in range(len(years)):
            v = pivot.values[i, j]
            if v > 0:
                ax.text(j, i, f"{v:.0f}", ha="center", va="center",
                        fontsize=6.5, color="white" if v > pivot.values.max() * 0.4 else MUTED_CLR)
    plt.colorbar(im, ax=ax, label="Minutes Listened", shrink=0.7)
    ax.set_title("🔥 Top 15 Artists × Year  (Minutes Listened)", fontsize=15, pad=14)
    save(fig, "03_top_artists_heatmap.png")


# ── Chart 4: Hourly Polar Chart ───────────────────────────────────────────────
def chart_hourly_polar() -> None:
    df = load_csv("hourly_distribution")
    plays_n = df["total_plays"].values / df["total_plays"].values.max()
    angles = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    width  = 2 * np.pi / 24 * 0.85
    fig = plt.figure(figsize=(8, 8))
    ax  = fig.add_subplot(111, polar=True)
    ax.set_facecolor(CARD_BG); fig.patch.set_facecolor(DARK_BG)
    ax.bar(angles, plays_n, width=width, bottom=0.1, align="center",
           color=[PALETTE[i % len(PALETTE)] for i in range(24)], alpha=0.85)
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
    ax.set_xticks(angles)
    ax.set_xticklabels([f"{h:02d}:00" for h in df["hour"].values], fontsize=7.5, color=TEXT_CLR)
    ax.yaxis.set_visible(False)
    ax.set_title("🕐 Listening Intensity by Hour of Day", fontsize=14, pad=22, color=TEXT_CLR)
    ax.spines["polar"].set_edgecolor(GRID_CLR)
    save(fig, "04_hourly_polar.png")


# ── Chart 5: New vs Familiar Artists (Stacked Area) ──────────────────────────
def chart_new_vs_familiar() -> None:
    monthly   = load_csv("monthly_listening_hours")
    discovery = load_csv("artist_discovery_per_month")
    df = monthly.merge(discovery, on=["year", "month"], how="left")
    df["new_artists_discovered"] = df["new_artists_discovered"].fillna(0)
    df["familiar"] = df["total_plays"] - df["new_artists_discovered"]
    label_col = next((c for c in ["year_month_x", "year_month"] if c in df.columns), None)
    df["label"] = df[label_col] if label_col else (
        df["year"].astype(str) + "-" + df["month"].apply(lambda m: f"{int(m):02d}")
    )
    fig, ax = plt.subplots(figsize=(16, 5))
    x = range(len(df))
    ax.stackplot(x, df["new_artists_discovered"], df["familiar"],
                 labels=["New Artist Plays", "Familiar Artist Plays"],
                 colors=[PALETTE[3], PALETTE[0]], alpha=0.8)
    ax.set_title("🌟 New vs Familiar Artist Plays per Month", fontsize=15, pad=14)
    ax.set_xlabel("Month"); ax.set_ylabel("Play Count")
    ax.set_xticks(list(x)[::6])
    ax.set_xticklabels(df["label"].iloc[::6], rotation=45, ha="right", fontsize=7)
    ax.legend(loc="upper left", facecolor=CARD_BG, edgecolor=GRID_CLR)
    ax.grid(axis="y", alpha=0.3)
    save(fig, "05_new_vs_familiar.png")


# ── Chart 6: Top-1 Concentration ─────────────────────────────────────────────
def chart_top1_concentration() -> None:
    df = load_csv("diversity_metrics")
    if "year_month" not in df.columns:
        df["year_month"] = df["year"].astype(str) + "-" + df["month"].apply(lambda m: f"{int(m):02d}")
    fig, ax = plt.subplots(figsize=(16, 4))
    x = range(len(df))
    ax.fill_between(x, df["top1_concentration"] * 100, alpha=0.3, color=PALETTE[1])
    ax.plot(x, df["top1_concentration"] * 100, color=PALETTE[1], linewidth=1.8)
    ax.axhline(df["top1_concentration"].mean() * 100, color=MUTED_CLR, linestyle="--",
               linewidth=1, label=f"Average {df['top1_concentration'].mean() * 100:.1f}%")
    ax.set_title("🎯 Top-1 Artist Concentration per Month  (% of all plays)", fontsize=15, pad=14)
    ax.set_xlabel("Month"); ax.set_ylabel("% of Plays")
    ax.set_xticks(list(x)[::6])
    ax.set_xticklabels(df["year_month"].iloc[::6], rotation=45, ha="right", fontsize=7)
    ax.legend(facecolor=CARD_BG, edgecolor=GRID_CLR)
    ax.grid(axis="y", alpha=0.4)
    save(fig, "06_top1_concentration.png")


# ── Chart 7: Year-over-Year Top 5 (Small Multiples) ──────────────────────────
def chart_top5_per_year() -> None:
    df    = load_csv("top_artists_by_year")
    years = sorted(df["year"].unique())
    cols  = 5
    rows  = (len(years) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(20, rows * 3.5))
    axes = axes.flatten()
    for i, yr in enumerate(years):
        ax   = axes[i]
        top5 = df[df["year"] == yr].nsmallest(5, "rank_in_year")
        names = [a[:18] + "…" if len(a) > 18 else a for a in top5["artist_name"]]
        bars  = ax.barh(range(len(names)), top5["total_minutes"].values,
                        color=[PALETTE[j % len(PALETTE)] for j in range(len(names))],
                        alpha=0.85, height=0.65)
        ax.set_yticks(range(len(names))); ax.set_yticklabels(names, fontsize=7)
        ax.set_title(str(yr), fontsize=11, color=TEXT_CLR)
        ax.grid(axis="x", alpha=0.3); ax.tick_params(axis="x", labelsize=6)
    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)
    fig.suptitle("🏆 Top 5 Artists per Year", fontsize=16, y=1.01, color=TEXT_CLR)
    plt.tight_layout()
    save(fig, "07_top5_per_year.png")


# ── Chart 8: Platform Evolution (Stacked Area) ───────────────────────────────
def chart_platform_evolution() -> None:
    df = load_csv("platform_usage")
    platforms = df.groupby("platform")["total_plays"].sum().nlargest(5).index.tolist()
    pivot = (df[df["platform"].isin(platforms)]
             .pivot_table(index="year", columns="platform", values="total_plays",
                          aggfunc="sum", fill_value=0))
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.stackplot(pivot.index, pivot.T.values,
                 labels=pivot.columns.tolist(),
                 colors=PALETTE[:len(pivot.columns)], alpha=0.82)
    ax.set_title("📱 Platform Evolution by Year", fontsize=15, pad=14)
    ax.set_xlabel("Year"); ax.set_ylabel("Play Count")
    ax.legend(loc="upper left", facecolor=CARD_BG, edgecolor=GRID_CLR, fontsize=9)
    ax.grid(axis="y", alpha=0.3); ax.set_xticks(pivot.index)
    save(fig, "08_platform_evolution.png")


# ── Chart 9: Hour × Day-of-Week Heatmap ──────────────────────────────────────
def chart_hour_day_heatmap() -> None:
    df   = load_csv("hour_day_heatmap")
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    pivot = df.pivot_table(index="day_of_week", columns="hour",
                           values="total_plays", aggfunc="sum", fill_value=0)
    pivot.index = [days[i] for i in pivot.index]
    cmap = LinearSegmentedColormap.from_list("heat", ["#141720", "#6c63ff", "#ff6584", "#f9a825"])
    fig, ax = plt.subplots(figsize=(16, 5))
    im = ax.imshow(pivot.values, aspect="auto", cmap=cmap, interpolation="nearest")
    ax.set_xticks(range(24)); ax.set_xticklabels([f"{h:02d}h" for h in range(24)], fontsize=7.5)
    ax.set_yticks(range(7)); ax.set_yticklabels(days, fontsize=9)
    plt.colorbar(im, ax=ax, label="Play Count", shrink=0.8)
    ax.set_title("🗓️  Listening Heatmap: Hour × Day of Week", fontsize=15, pad=14)
    save(fig, "09_hour_day_heatmap.png")


# ── Chart 10: Diversity Dashboard (multi-panel) ───────────────────────────────
def chart_diversity_dashboard() -> None:
    df = load_csv("diversity_metrics")
    if "year_month" not in df.columns:
        df["year_month"] = df["year"].astype(str) + "-" + df["month"].apply(lambda m: f"{int(m):02d}")
    fig = plt.figure(figsize=(18, 10))
    fig.patch.set_facecolor(DARK_BG)
    gs = gridspec.GridSpec(3, 1, hspace=0.45)
    x  = range(len(df))
    xt = list(x)[::6]
    xl = df["year_month"].iloc[::6].tolist()

    def _panel(ax, col_key, fallback, colour, ylabel, title):
        col = col_key if col_key in df.columns else fallback
        ax.fill_between(x, df[col], alpha=0.25, color=colour)
        ax.plot(x, df[col], color=colour, linewidth=2)
        ax.set_ylabel(ylabel); ax.set_title(title, pad=8)
        ax.set_xticks(xt); ax.set_xticklabels(xl, rotation=40, ha="right", fontsize=7)
        ax.grid(axis="y", alpha=0.3)

    ax1 = fig.add_subplot(gs[0])
    _panel(ax1, "shannon_entropy_rolling3", "shannon_entropy",
           PALETTE[2], "Shannon Entropy H", "Shannon Entropy (Diversity Index)")
    if "is_change_point" in df.columns:
        for idx_v, row in df[df["is_change_point"] == 1].iterrows():
            ax1.axvline(df.index.get_loc(idx_v), color=PALETTE[1], linewidth=0.9, linestyle=":", alpha=0.7)

    ax2 = fig.add_subplot(gs[1])
    col2 = "new_artist_ratio_rolling3" if "new_artist_ratio_rolling3" in df.columns else "new_artist_ratio"
    ax2.fill_between(x, df[col2] * 100, alpha=0.25, color=PALETTE[3])
    ax2.plot(x, df[col2] * 100, color=PALETTE[3], linewidth=2)
    ax2.set_ylabel("New Artist Ratio (%)"); ax2.set_title("Monthly New Artist Discovery Rate", pad=8)
    ax2.set_xticks(xt); ax2.set_xticklabels(xl, rotation=40, ha="right", fontsize=7)
    ax2.grid(axis="y", alpha=0.3)

    ax3 = fig.add_subplot(gs[2])
    col3 = "top1_concentration_rolling3" if "top1_concentration_rolling3" in df.columns else "top1_concentration"
    ax3.fill_between(x, df[col3] * 100, alpha=0.25, color=PALETTE[1])
    ax3.plot(x, df[col3] * 100, color=PALETTE[1], linewidth=2)
    ax3.set_ylabel("Top-1 Conc. (%)"); ax3.set_title("Top Artist Concentration (Obsession Index)", pad=8)
    ax3.set_xticks(xt); ax3.set_xticklabels(xl, rotation=40, ha="right", fontsize=7)
    ax3.grid(axis="y", alpha=0.3)

    fig.suptitle("🎼 Music Diversity Dashboard  (10-Year View)", fontsize=17, y=1.01, color=TEXT_CLR)
    save(fig, "10_diversity_dashboard.png")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    log.info("=" * 55)
    log.info("  STEP 05 — VISUALIZATIONS")
    log.info("=" * 55)

    steps = [
        ("01 — Listening Timeline",      chart_listening_timeline),
        ("02 — Diversity Index",         chart_diversity_index),
        ("03 — Top Artists Heatmap",     chart_top_artists_heatmap),
        ("04 — Hourly Polar Chart",      chart_hourly_polar),
        ("05 — New vs Familiar Artists", chart_new_vs_familiar),
        ("06 — Top-1 Concentration",     chart_top1_concentration),
        ("07 — Top 5 Per Year",          chart_top5_per_year),
        ("08 — Platform Evolution",      chart_platform_evolution),
        ("09 — Hour × Day Heatmap",      chart_hour_day_heatmap),
        ("10 — Diversity Dashboard",     chart_diversity_dashboard),
    ]

    for label, fn in steps:
        try:
            log.info("Generating: %s", label)
            fn()
        except Exception as e:
            log.error("Failed: %s — %s", label, e)

    log.info("All charts saved to: %s", CHARTS_DIR)
    log.info("Project complete! Open output/charts/ to view your visualizations.")


if __name__ == "__main__":
    main()
