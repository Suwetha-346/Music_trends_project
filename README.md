#  Spotify Music Evolution — 10-Year Analytics Project

A professional end-to-end Data Analytics project that analyzes and visualizes **10 years of personal Spotify listening behavior (2015–2024)** using synthetic streaming data. The project demonstrates a complete analytics pipeline including data generation, ETL processing, SQL database integration, statistical diversity analysis, and advanced dark-theme visualizations.

This project combines:
- Data Engineering
- Data Analytics
- SQL
- Python Visualization
- Statistical Analysis
- ETL Pipeline Design

---

#  Table of Contents

- Overview
- Project Highlights
- Objectives
- Architecture
- Technologies Used
- Project Structure
- Dataset Information
- ETL Pipeline
- Database Design
- Music Diversity Index
- Visualizations
- Installation
- How to Run the Project
- Sample Insights
- Future Enhancements
- Author

---

#  Overview

Music listening habits change over time based on mood, trends, lifestyle, and preferences. This project analyzes how listening behavior evolved over a decade by simulating Spotify streaming activity.

The pipeline:
- Generates realistic Spotify streaming data
- Cleans and transforms the data
- Loads data into a relational database
- Performs SQL analytics
- Calculates a custom Music Diversity Index
- Produces professional analytical charts

The final output provides insights into:
- Genre evolution
- Artist loyalty
- Listening diversity
- Seasonal trends
- Listening behavior patterns

---

#  Project Highlights

| Metric | Value |
|--------|-------|
| Records processed | ~155,000 stream events |
| Date range | Jan 2015 – Dec 2024 |
| Artists modelled | 110 |
| Genre eras | 11 |
| SQL tables | 4 |
| Charts generated | 10 |
| Diversity algorithm | Shannon Entropy + Pielou’s Evenness |

---

#  Objectives

The main objectives of this project are:

- Simulate realistic Spotify listening behavior
- Build a scalable ETL pipeline
- Store and analyze streaming data using SQL
- Measure music diversity mathematically
- Create publication-quality visualizations
- Demonstrate real-world analytics workflow

---

#  Technologies Used

## Programming Language
- Python

## Libraries
- Pandas
- NumPy
- Matplotlib
- SQLite3
- SQLAlchemy
- SciPy

## Database
- SQLite
- MySQL (Optional)

## Visualization
- Matplotlib (Dark Theme)

## Development Tools
- VS Code
- Jupyter Notebook



#  Dataset Information

The project uses synthetically generated Spotify streaming data containing:

- Song Name
- Artist Name
- Genre
- Album
- Stream Timestamp
- Listening Duration
- Skip Rate
- User Mood Tags
- Yearly Listening Trends

The dataset simulates realistic music listening behavior over 10 years.

---

#  ETL Pipeline

The ETL (Extract, Transform, Load) pipeline includes:

## 1. Data Extraction
Synthetic Spotify streaming JSON files are generated.

## 2. Data Cleaning
The pipeline:
- Removes duplicates
- Handles missing values
- Standardizes formats
- Filters invalid records

## 3. Feature Engineering
Additional features created:
- Listening hour
- Day of week
- Listening season
- Genre categories
- Yearly trends

## 4. Database Loading
Cleaned data is loaded into SQLite/MySQL tables.

---

#  Database Design

The project stores processed data in relational tables:

| Table | Description |
|------|-------------|
| artists | Artist metadata |
| tracks | Track information |
| streams | Listening history |
| diversity_metrics | Diversity scores |

---

#  Music Diversity Index

A custom **Music Diversity Index** is calculated using:

## Shannon Entropy
Measures randomness and variety in music listening behavior.

## Pielou’s Evenness
Measures how evenly listening time is distributed across genres.

The diversity score helps analyze:
- Genre exploration
- Artist diversity
- Listening balance
- Evolution of taste over time

---

#  Visualizations

The project generates 10 professional dark-theme visualizations.

## Included Charts

- Yearly Listening Trends
- Top Artists Over Time
- Genre Popularity Evolution
- Listening Heatmaps
- Monthly Streaming Distribution
- Diversity Index Trends
- Artist Loyalty Analysis
- Listening Time Patterns
- Most Streamed Tracks
- Seasonal Genre Preferences

All charts are exported as high-quality PNG images.

---

#  Installation

## Clone Repository

```bash
git clone https://github.com/yourusername/spotify_music_evolution.git
cd spotify_music_evolution
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

---

## Activate Environment

### Windows
```bash
venv\Scripts\activate
```

### Linux/Mac
```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

#  How to Run the Project

## Step 1: Generate Synthetic Data

```bash
python generate_synthetic_data.py
```

---

## Step 2: Clean and Process Data

```bash
python scripts/01_data_cleaning.py
```

---

## Step 3: Load Data into Database

```bash
python scripts/02_load_to_db.py
```

---

## Step 4: Run Analysis Queries

```bash
python scripts/03_analysis_queries.py
```

---

## Step 5: Calculate Diversity Index

```bash
python scripts/04_diversity_index.py
```

---

## Step 6: Generate Visualizations

```bash
python scripts/05_visualizations.py
```

---

#  Sample Insights

Example analytical findings:

- Music diversity increased significantly after 2020.
- Indie and Lo-fi genres showed rapid growth.
- Listening behavior peaks during late-night hours.
- Artist loyalty reduced over time due to genre exploration.
- Seasonal listening trends vary across years.

---

#  Future Enhancements

Possible improvements:

- Spotify API integration
- Real user streaming data support
- Interactive dashboard using Streamlit
- Power BI integration
- Real-time analytics pipeline
- Recommendation system
- Machine learning-based mood prediction

---

#  Skills Demonstrated

This project demonstrates:

✅ Data Analytics  
✅ Data Engineering  
✅ ETL Pipelines  
✅ SQL & Database Management  
✅ Python Programming  
✅ Data Visualization  
✅ Statistical Analysis  
✅ Feature Engineering  
✅ Analytical Reporting  

---


## Skills
- Python
- SQL
- Power BI
- Data Analytics
- Machine Learning
