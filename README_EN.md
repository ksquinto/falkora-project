# 🌌 FALKORA

**Where Music Becomes Stars** — AI-powered music success prediction platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React 18+](https://img.shields.io/badge/React-18+-61dafb.svg)](https://react.dev/)

---

## What is Falkora?

Falkora is an AI-powered platform that analyzes audio tracks and predicts their commercial potential. Using machine learning, it compares your song against real hits in the market to determine if it will be a **Supernova** (blockbuster), **Rising Star** (high potential), or **Dormant Star** (low potential).

Perfect for artists, producers, promoters, and record labels who want data-driven insights before investing in a track.

---

## Key Features

- 🔬 **Audio DNA Analysis** — Extracts 15+ audio characteristics (tempo, energy, danceability, etc.)
- 🎯 **Hit Prediction** — XGBoost model trained on 89,740 songs with 80%+ accuracy
- 🌌 **Interactive Galaxy** — Visualize your song in a 2D map of 3,000 reference tracks
- 📊 **Detailed Diagnosis** — Compare against genre hits with visual breakdowns
- 📥 **Professional Reports** — Export analysis to PDF for labels and promoters
- 🌍 **Dual Analysis** — Compare within genre or across all genres

---

## The Methodology

### 1️⃣ **Audio Feature Extraction**
Using **Essentia**, we extract 15 key audio characteristics:
- **Rhythm**: Danceability, Tempo, Time Signature
- **Energy**: Energy, Loudness, Acousticness
- **Emotion**: Valence (positivity), Liveness, Speechiness
- **Instrumentation**: Instrumentalness, Key, Mode

These features are normalized to [0,1] range for consistency.

### 2️⃣ **Hit Classification**
We trained an **XGBoost model** on 89,740 songs labeled as:
- **Hit** (songs with 10M+ streams or major radio play)
- **Mid** (songs with moderate success)
- **Flop** (songs with low engagement)

**Model Performance**: 80-82% accuracy per genre

### 3️⃣ **Comparison & Gravity Score**
The model calculates:
- How your track compares against hits in its genre
- **Gravity Score**: 0-100% similarity to successful songs
- **Feature Gaps**: Which characteristics help or hurt your track

### 4️⃣ **Visualization**
- **Radar Chart**: Your track vs. genre average (interactive)
- **Galaxy Map**: 2,500 reference songs plotted in 2D space using UMAP
- **Tooltips**: Explanations of each metric in plain language

---

## Quick Start

### Requirements
- Python 3.8+ (Windows)
- Node.js 16+ (Windows)
- WSL2 with Ubuntu (for Essentia)

### Installation (5 minutes)

```bash
# Backend
cd falkora-backend
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
python -m uvicorn main:app --port 8000

# Frontend (new terminal)
cd falkora-frontend
npm install
npm run dev

# Open http://localhost:5173
```

---

## Architecture

```
Frontend (React)
    ↓ Upload WAV/MP3
Backend (FastAPI)
    ↓ Calls WSL
Essentia (Ubuntu)
    ↓ Extract 15 features
XGBoost Model
    ↓ Predict: Hit/Mid/Flop
UMAP Visualization
    ↓ Plot in 2D Galaxy
User sees: Veredicto + Galaxy + Diagnosis
```

---

## Data

- **89,740 tracks** from Spotify, YouTube, and music databases
- **10+ genres** including Salsa, Reggaeton, Pop, Trap, etc.
- **Accuracy**: 80-82% per genre
- **Model**: XGBoost with feature engineering

---

## Output

### For Each Track:
1. **Verdict** — Supernova / Rising Star / Dormant Star
2. **Gravity Score** — % similarity to hits (0-100%)
3. **Audio Metrics** — All 15 characteristics with values
4. **Diagnostic Report** — PDF with analysis & recommendations

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS, Framer Motion |
| Backend | FastAPI, XGBoost, UMAP, Pandas |
| Audio | Essentia (feature extraction) |
| Database | CSV + Pickle models |

---

## Use Cases

👨‍🎵 **Artists**: Know if your track has commercial potential before release  
🎼 **Producers**: Understand what makes hits and adjust your mix  
🏢 **Labels**: Data-driven A&R decisions  
📻 **Promoters**: Predict playlist success before pitching  

---

## Results Interpretation

| Score | Meaning |
|-------|---------|
| **80-100%** | Supernova — Ready to release, high hit potential |
| **50-79%** | Rising Star — Good potential, minor tweaks suggested |
| **0-49%** | Dormant Star — Consider changes before release |


## Support

- 📖 Full documentation in `docs/`
- 🐛 Report issues on GitHub
- 💬 Discussions for questions

---

*Where Music Becomes Stars* 🌌
