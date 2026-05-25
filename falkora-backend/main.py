"""
╔══════════════════════════════════════════════════════════════════╗
║                    🌌  FALKORA — Backend API                      ║
║                                                                  ║
║  "Where music becomes stars."                                    ║
║                                                                  ║
║  Every track enters Falkora as an unknown star. Its gravity,     ║
║  resonance, and energy determine whether it fades... or          ║
║  becomes a supernova.                                            ║
╚══════════════════════════════════════════════════════════════════╝

EJECUTAR:
    uvicorn main:app --reload --port 8000

DOCS interactivas:
    http://localhost:8000/docs
"""
import os
import tempfile
import pandas as pd

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal

import config
from core.predictor import get_model
from core import galaxy as galaxy_mod
from core import diagnosis as diag_mod
from core import siblings as sib_mod

# ── App ───────────────────────────────────────────────────────────
app = FastAPI(
    title="Falkora API",
    description="The universe of musical potential. Where tracks find their orbit.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Estado global (cargado al inicio) ─────────────────────────────
STATE = {
    "df": None,
    "galaxy_df": None,
    "reducer": None,
    "model": None,
}


@app.on_event("startup")
def startup():
    """Carga modelo, dataset y construye la galaxia al arrancar."""
    print("🌌 Iniciando Falkora...")

    # Modelo
    STATE["model"] = get_model()
    print(f"   ✅ Modelo cargado: {type(STATE['model'].model).__name__}")

    # Dataset
    df = pd.read_csv(config.DATA_PATH)
    df = df.dropna(subset=["track_name", "album_name"])
    df = df.drop_duplicates(subset=["track_id"])
    df["duration_min"] = df["duration_ms"] / 60000
    df["explicit"] = df["explicit"].astype(int)
    STATE["df"] = df
    print(f"   ✅ Dataset: {len(df):,} tracks")

    # Galaxia (UMAP 2D con muestreo)
    try:
        # Muestreo: máximo 3000 canciones para visualización clara
        sample_size = min(3000, len(df))
        df_sample = df.sample(n=sample_size, random_state=42)
        print(f"   🔬 Muestreando {sample_size:,} canciones para galaxia...")
        galaxy_df, reducer = galaxy_mod.build_galaxy(df_sample, dimensions=2)
        STATE["galaxy_df"] = galaxy_df
        STATE["reducer"] = reducer
        print(f"   ✅ Galaxia construida (2D, {sample_size:,} estrellas)")
    except Exception as e:
        print(f"   ⚠️  Galaxia no construida: {e}")

    print("🚀 Falkora lista — http://localhost:8000/docs")


# ── Modelos de request ────────────────────────────────────────────
class TrackFeatures(BaseModel):
    danceability: float
    energy: float
    loudness: float
    speechiness: float
    acousticness: float
    instrumentalness: float
    liveness: float
    valence: float
    tempo: float
    key: int = 0
    mode: int = 1
    time_signature: int = 4
    duration_min: float = 3.5
    explicit: int = 0
    genre: str = "latin"


class AnalysisRequest(BaseModel):
    features: TrackFeatures
    mode: Literal["intragalactic", "extragalactic"] = "intragalactic"


# ── ENDPOINTS ─────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "app": "Falkora",
        "tagline": "Where music becomes stars.",
        "status": "online",
        "tracks_in_galaxy": len(STATE["df"]) if STATE["df"] is not None else 0,
    }


@app.post("/analyze")
def analyze(req: AnalysisRequest):
    """
    Análisis completo de un track: veredicto + diagnóstico +
    gravity score + hermanos sonoros + posición en galaxia.
    Todo en un solo llamado, según el modo elegido.
    """
    feats = req.features.dict()
    genre = feats.pop("genre")
    mode  = req.mode
    df    = STATE["df"]

    # 1. Veredicto (predicción)
    prediction = STATE["model"].predict(feats, genre)

    # 2. Diagnóstico (brechas + gravity + explicación)
    diagnosis = diag_mod.diagnose(feats, df, genre, mode)

    # 3. Hermanos sonoros
    siblings = sib_mod.find_siblings(
        feats, df,
        genre=genre if mode == "intragalactic" else None,
        only_hits=True
    )

    # 4. Posición en la galaxia (cometa entrante)
    position = None
    if STATE["reducer"] is not None:
        try:
            position = galaxy_mod.locate_track(STATE["reducer"], feats)
        except Exception:
            position = None

    return {
        "verdict":   prediction,
        "diagnosis": diagnosis,
        "siblings":  siblings,
        "position":  position,
        "mode":      mode,
        "genre":     genre,
    }


@app.post("/analyze/upload")
async def analyze_upload(
    file: UploadFile = File(...),
    genre: str = "latin",
    mode: str = "intragalactic"
):
    """
    Sube un WAV/MP3 → extrae features con Essentia (vía WSL) → análisis completo.
    Esta es la ventaja competitiva: analiza tracks NO publicados.
    """
    from core import audio_extractor

    # Guardar archivo temporal
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Extraer features (Essentia vía WSL o fallback librosa)
        feats = audio_extractor.extract_features(tmp_path)
        
        # Verificar si hubo error
        if isinstance(feats, dict) and feats.get("success") == False:
            # Intentar con librosa como fallback
            print(f"   ⚠️  Essentia falló, usando librosa fallback...")
            feats = audio_extractor.extract_features_librosa(tmp_path)
            if isinstance(feats, dict) and feats.get("success") == False:
                raise HTTPException(500, detail=feats.get("error", "Feature extraction failed"))

        # Quitar metadata de confianza para la predicción
        feats_clean = {k: v for k, v in feats.items() if not k.startswith("_")}

        # Análisis completo
        prediction = STATE["model"].predict(feats_clean, genre)
        diagnosis  = diag_mod.diagnose(feats_clean, STATE["df"], genre, mode)
        siblings   = sib_mod.find_siblings(
            feats_clean, STATE["df"],
            genre=genre if mode == "intragalactic" else None,
            only_hits=True
        )
        
        position = None
        if STATE["reducer"] is not None:
            try:
                position = galaxy_mod.locate_track(STATE["reducer"], feats_clean)
            except Exception:
                position = None

        return {
            "filename":  file.filename,
            "extracted_features": feats,
            "verdict":   prediction,
            "diagnosis": diagnosis,
            "siblings":  siblings,
            "position":  position,
            "mode":      mode,
            "genre":     genre,
        }
    finally:
        os.unlink(tmp_path)


@app.get("/galaxy")
def get_galaxy(mode: str = "extragalactic", genre: Optional[str] = None):
    """
    Devuelve el mapa completo de estrellas para renderizar la galaxia.
    Filtrable por género. El modo cambia cómo se clasifican las estrellas.
    """
    if STATE["galaxy_df"] is None:
        raise HTTPException(503, "Galaxia no disponible — UMAP no se construyó")

    gdf = STATE["galaxy_df"]
    if genre:
        gdf = gdf[gdf["track_genre"] == genre]

    stars = galaxy_mod.galaxy_to_json(gdf, mode=mode)

    return {
        "mode":   mode,
        "genre":  genre or "all",
        "count":  len(stars),
        "stars":  stars,
    }


@app.get("/genres")
def get_genres():
    """Lista de géneros disponibles en la galaxia."""
    if STATE["df"] is None:
        return {"genres": []}
    counts = STATE["df"]["track_genre"].value_counts()
    return {
        "genres": [
            {"name": g, "tracks": int(n), "is_latin": g in config.LATIN_GENRES}
            for g, n in counts.items()
        ]
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded":  STATE["model"] is not None,
        "galaxy_ready":  STATE["galaxy_df"] is not None,
        "tracks":        len(STATE["df"]) if STATE["df"] is not None else 0,
    }
