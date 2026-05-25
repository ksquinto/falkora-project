"""
╔══════════════════════════════════════════════════════════╗
║  FALKORA — Configuración central                         ║
╚══════════════════════════════════════════════════════════╝
"""
import os

# ── Rutas ─────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_PATH  = os.path.join(BASE_DIR, "data", "dataset.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")
CACHE_PATH = os.path.join(BASE_DIR, "data", "galaxy_cache.json")

MODEL_PATH        = os.path.join(MODELS_DIR, "hit_score_model.pkl")
GENRE_ENCODER     = os.path.join(MODELS_DIR, "genre_encoder.pkl")
LABEL_ENCODER     = os.path.join(MODELS_DIR, "label_encoder.pkl")

# ── Features que usa el modelo ────────────────────────────
FEATURES = [
    "danceability", "energy", "loudness", "speechiness",
    "acousticness", "instrumentalness", "liveness",
    "valence", "tempo", "explicit", "key", "mode",
    "time_signature", "genre_encoded", "duration_min"
]

# Features comparables en el diagnóstico (0-1, interpretables)
DIAGNOSIS_FEATURES = [
    "danceability", "energy", "valence",
    "acousticness", "speechiness", "liveness"
]

# ── Géneros ───────────────────────────────────────────────
LATIN_GENRES = [
    "latin", "latino", "mpb", "pagode", "reggae",
    "reggaeton", "salsa", "sertanejo", "tango"
]

# ── Umbrales de popularidad ───────────────────────────────
HIT_THRESHOLD = 60   # popularity >= 60 → hit (extragaláctico)
MID_THRESHOLD = 30

# Para modo intragaláctico — percentil dentro del género
SUPERNOVA_PERCENTILE = 90   # top 10% de su género = supernova
RISING_PERCENTILE    = 70   # top 30% = rising star

# ── Galaxia (UMAP) ────────────────────────────────────────
UMAP_NEIGHBORS    = 30   # Más vecinos = clusters más definidos
UMAP_MIN_DIST     = 0.3  # Más distancia = puntos más dispersos
UMAP_RANDOM_STATE = 42

# ── Hermanos sonoros ──────────────────────────────────────
N_SIBLINGS = 5

# ── CORS (para el front) ──────────────────────────────────
ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:5173", "*"]
