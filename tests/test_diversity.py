"""
tests/test_diversity.py
=======================
Unit tests for the Shannon Entropy and Diversity Index logic.

Run with:
    pytest tests/ -v
"""

import sys
import os
import math
import pandas as pd
import numpy as np
import pytest

# Make project root importable from any working directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.diversity_core import shannon_entropy, evenness, detect_change_points


# ─── shannon_entropy ──────────────────────────────────────────────────────────

class TestShannonEntropy:

    def test_uniform_distribution_is_maximum_entropy(self):
        """With N equally probable artists, H = ln(N) — the theoretical max."""
        n = 10
        series = pd.Series(list(range(n)) * 20)   # 20 plays each → perfectly uniform
        H = shannon_entropy(series)
        expected = math.log(n)
        assert abs(H - expected) < 1e-9, f"Expected H≈{expected:.4f}, got {H:.4f}"

    def test_single_artist_monopoly_is_zero_entropy(self):
        """If one artist gets 100% of plays, H must equal 0."""
        series = pd.Series(["Artist A"] * 500)
        H = shannon_entropy(series)
        assert H == pytest.approx(0.0, abs=1e-9), f"Expected H=0, got {H}"

    def test_two_artists_equal_split(self):
        """Two artists, 50/50 split → H = ln(2) ≈ 0.6931."""
        series = pd.Series(["A"] * 50 + ["B"] * 50)
        H = shannon_entropy(series)
        assert H == pytest.approx(math.log(2), rel=1e-6)

    def test_more_artists_increases_entropy(self):
        """Adding more distinct artists should never decrease entropy."""
        s2 = pd.Series(["A"] * 50 + ["B"] * 50)
        s5 = pd.Series(["A"] * 20 + ["B"] * 20 + ["C"] * 20 + ["D"] * 20 + ["E"] * 20)
        assert shannon_entropy(s5) > shannon_entropy(s2)

    def test_single_element_series(self):
        """A series with exactly one element should return H=0."""
        series = pd.Series(["Solo Artist"])
        H = shannon_entropy(series)
        assert H == pytest.approx(0.0, abs=1e-9)

    def test_returns_float(self):
        series = pd.Series(["A", "B", "A", "C"])
        assert isinstance(shannon_entropy(series), float)


# ─── evenness ─────────────────────────────────────────────────────────────────

class TestEvenness:

    def test_single_artist_returns_zero(self):
        """With n=1 unique artist, log(1) = 0, so evenness must return 0."""
        assert evenness(H=0.0, n_unique=1) == pytest.approx(0.0)

    def test_zero_unique_returns_zero(self):
        """Guard against log(0): n_unique=0 should return 0 safely."""
        assert evenness(H=0.0, n_unique=0) == pytest.approx(0.0)

    def test_perfect_evenness_is_one(self):
        """Uniform distribution → H = ln(n) → E = H/ln(n) = 1.0."""
        n = 8
        H = math.log(n)
        E = evenness(H, n)
        assert E == pytest.approx(1.0, rel=1e-9)

    def test_evenness_in_range_zero_to_one(self):
        """Evenness must always be in [0, 1]."""
        series = pd.Series(["A"] * 70 + ["B"] * 20 + ["C"] * 10)
        H = shannon_entropy(series)
        E = evenness(H, series.nunique())
        assert 0.0 <= E <= 1.0


# ─── detect_change_points ─────────────────────────────────────────────────────

class TestDetectChangePoints:

    def _make_metrics(self, entropy_values):
        """Helper: build a minimal diversity_metrics DataFrame."""
        return pd.DataFrame({
            "year":           range(2015, 2015 + len(entropy_values)),
            "month":          [1] * len(entropy_values),
            "shannon_entropy": entropy_values,
        })

    def test_no_crash_on_flat_series(self):
        """A completely flat entropy series should not raise and find 0 change points."""
        df = self._make_metrics([3.0] * 24)
        result = detect_change_points(df.copy())
        # std of a constant is 0 → threshold is 0 → delta==0 never > threshold
        assert "is_change_point" in result.columns
        assert result["is_change_point"].sum() == 0

    def test_detects_obvious_spike(self):
        """A large sudden spike should always be flagged as a change point."""
        values = [3.0] * 10 + [0.1] + [3.0] * 10   # dramatic drop at index 10
        df = self._make_metrics(values)
        result = detect_change_points(df.copy())
        spike_row = result.iloc[10]
        assert spike_row["is_change_point"] == 1

    def test_output_columns_present(self):
        df = self._make_metrics([2.5 + 0.1 * i for i in range(12)])
        result = detect_change_points(df.copy())
        assert "entropy_delta"   in result.columns
        assert "is_change_point" in result.columns

    def test_is_change_point_is_binary(self):
        """The flag column should only contain 0 or 1."""
        values = [1.0, 1.1, 5.0, 1.0, 1.1, 1.2, 1.0]
        df = self._make_metrics(values)
        result = detect_change_points(df.copy())
        unique_vals = set(result["is_change_point"].unique())
        assert unique_vals.issubset({0, 1})
