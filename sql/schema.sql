-- ============================================================
-- Spotify Music Evolution — Database Schema
-- ============================================================
-- Run this file to create the database and tables.
-- Usage: mysql -u root -p < sql/schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS spotify_evolution
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE spotify_evolution;

-- ─────────────────────────────────────────────────────────────
-- Dimension: Artists
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS artists (
    artist_id   INT AUTO_INCREMENT PRIMARY KEY,
    artist_name VARCHAR(500) NOT NULL,
    UNIQUE KEY uq_artist_name (artist_name(191))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────────────────────
-- Dimension: Tracks
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tracks (
    track_id     INT AUTO_INCREMENT PRIMARY KEY,
    track_name   VARCHAR(500) NOT NULL,
    album_name   VARCHAR(500),
    artist_id    INT NOT NULL,
    spotify_uri  VARCHAR(200),
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────────────────────
-- Fact: Streams
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS streams (
    stream_id      INT AUTO_INCREMENT PRIMARY KEY,
    track_id       INT NOT NULL,
    played_at      DATETIME NOT NULL,
    ms_played      INT NOT NULL,
    minutes_played DECIMAL(10, 2) NOT NULL,
    platform       VARCHAR(100),
    country        VARCHAR(10),
    reason_start   VARCHAR(50),
    reason_end     VARCHAR(50),
    shuffle        BOOLEAN DEFAULT FALSE,
    skipped        BOOLEAN DEFAULT FALSE,
    year           SMALLINT NOT NULL,
    month          TINYINT  NOT NULL,
    day_of_week    TINYINT  NOT NULL,   -- 0=Mon, 6=Sun
    hour           TINYINT  NOT NULL,
    FOREIGN KEY (track_id) REFERENCES tracks(track_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────────────────────
-- Indexes for query performance
-- ─────────────────────────────────────────────────────────────
CREATE INDEX idx_streams_year         ON streams(year);
CREATE INDEX idx_streams_year_month   ON streams(year, month);
CREATE INDEX idx_streams_played_at    ON streams(played_at);
CREATE INDEX idx_streams_skipped      ON streams(skipped);
CREATE INDEX idx_tracks_artist        ON tracks(artist_id);

-- ─────────────────────────────────────────────────────────────
-- Diversity Metrics (pre-computed monthly)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS diversity_metrics (
    metric_id          INT AUTO_INCREMENT PRIMARY KEY,
    year               SMALLINT NOT NULL,
    month              TINYINT  NOT NULL,
    total_plays        INT      NOT NULL,
    unique_artists     INT      NOT NULL,
    shannon_entropy    DECIMAL(10, 6) NOT NULL,
    normalized_entropy DECIMAL(10, 6) NOT NULL,   -- 0-1 scale (Evenness)
    new_artist_ratio   DECIMAL(10, 6) NOT NULL,   -- % artists heard for first time
    top1_concentration DECIMAL(10, 6) NOT NULL,   -- % plays by #1 artist
    UNIQUE KEY uq_year_month (year, month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
