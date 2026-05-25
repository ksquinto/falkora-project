"""
╔══════════════════════════════════════════════════════════╗
║  FALKORA — La Galaxia (Orbit Mapping con UMAP)           ║
║                                                          ║
║  Proyecta las 15 dimensiones del audio a un mapa 2D/3D   ║
║  donde la cercanía = similitud sonora. Cada canción es   ║
║  una estrella; los hits son supernovas brillantes.       ║
╚══════════════════════════════════════════════════════════╝
"""
import pandas as pd
import numpy as np
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


# Features que definen la posición en la galaxia (audio puro)
GALAXY_FEATURES = [
    "danceability", "energy", "loudness", "speechiness",
    "acousticness", "instrumentalness", "liveness",
    "valence", "tempo"
]


def build_galaxy(df: pd.DataFrame, dimensions: int = 2) -> pd.DataFrame:
    """
    Construye la galaxia: proyecta las canciones a 2D/3D con UMAP.
    Retorna el df con columnas star_x, star_y (y star_z si 3D).
    """
    from sklearn.preprocessing import StandardScaler
    import umap

    X = df[GALAXY_FEATURES].copy()
    X_scaled = StandardScaler().fit_transform(X)

    reducer = umap.UMAP(
        n_neighbors=config.UMAP_NEIGHBORS,
        min_dist=config.UMAP_MIN_DIST,
        n_components=dimensions,
        random_state=config.UMAP_RANDOM_STATE,
        metric="euclidean"
    )
    embedding = reducer.fit_transform(X_scaled)

    df = df.copy()
    df["star_x"] = embedding[:, 0]
    df["star_y"] = embedding[:, 1]
    if dimensions == 3:
        df["star_z"] = embedding[:, 2]

    # Guardar el reducer para ubicar tracks nuevos después
    return df, reducer


def classify_star(popularity: float, genre_percentile: float = None) -> dict:
    """
    Clasifica una estrella según la narrativa Falkora.
    Si se pasa genre_percentile, usa modo intragaláctico.
    """
    if genre_percentile is not None:
        # Modo intragaláctico — relativo al género
        if genre_percentile >= config.SUPERNOVA_PERCENTILE:
            star_type = "supernova"
        elif genre_percentile >= config.RISING_PERCENTILE:
            star_type = "rising"
        else:
            star_type = "dormant"
    else:
        # Modo extragaláctico — absoluto
        if popularity >= config.HIT_THRESHOLD:
            star_type = "supernova"
        elif popularity >= config.MID_THRESHOLD:
            star_type = "rising"
        else:
            star_type = "dormant"

    visual = {
        "supernova": {"size": 4.0, "color": "#39ff6a", "glow": True,  "label": "Supernova"},
        "rising":    {"size": 2.5, "color": "#f9c80e", "glow": False, "label": "Rising Star"},
        "dormant":   {"size": 1.5, "color": "#ff3864", "glow": False, "label": "Dormant Star"},
    }
    return {"type": star_type, **visual[star_type]}


def galaxy_to_json(df: pd.DataFrame, mode: str = "extragalactic") -> list:
    """
    Convierte la galaxia a JSON para el frontend.
    mode: 'extragalactic' (absoluto) o 'intragalactic' (percentil por género).
    """
    stars = []

    if mode == "intragalactic":
        # Calcular percentil de popularidad dentro de cada género
        df = df.copy()
        df["genre_pct"] = df.groupby("track_genre")["popularity"].rank(pct=True) * 100

    for _, row in df.iterrows():
        pct = row.get("genre_pct") if mode == "intragalactic" else None
        star = classify_star(row["popularity"], pct)
        stars.append({
            "id":         row.get("track_id", ""),
            "name":       row.get("track_name", ""),
            "artist":     row.get("artists", ""),
            "genre":      row.get("track_genre", ""),
            "popularity": int(row["popularity"]),
            "x":          round(float(row["star_x"]), 3),
            "y":          round(float(row["star_y"]), 3),
            "z":          round(float(row["star_z"]), 3) if "star_z" in row else 0,
            "star_type":  star["type"],
            "size":       star["size"],
            "color":      star["color"],
            "glow":       star["glow"],
        })
    return stars


def locate_track(reducer, track_features: dict) -> dict:
    """
    Ubica un track nuevo en la galaxia existente (el cometa entrante).
    """
    from sklearn.preprocessing import StandardScaler

    vec = np.array([[track_features[f] for f in GALAXY_FEATURES]])
    # Nota: en producción hay que usar el MISMO scaler del build_galaxy
    embedding = reducer.transform(vec)

    return {
        "x": round(float(embedding[0, 0]), 3),
        "y": round(float(embedding[0, 1]), 3),
        "z": round(float(embedding[0, 2]), 3) if embedding.shape[1] == 3 else 0,
    }
