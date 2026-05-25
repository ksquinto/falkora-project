"""
╔══════════════════════════════════════════════════════════╗
║  FALKORA — Stellar Siblings (Hermanos Sonoros)           ║
║                                                          ║
║  Encuentra las canciones más cercanas en el espacio       ║
║  sonoro que SÍ fueron hits — para que el artista          ║
║  estudie qué hicieron diferente.                         ║
╚══════════════════════════════════════════════════════════╝
"""
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


SIBLING_FEATURES = [
    "danceability", "energy", "loudness", "speechiness",
    "acousticness", "instrumentalness", "liveness", "valence", "tempo"
]


def find_siblings(track_features: dict, df: pd.DataFrame,
                  genre: str = None, only_hits: bool = True,
                  n: int = None) -> list:
    """
    Encuentra las n canciones más parecidas al track.

    - genre: si se especifica, busca solo en ese género (intragaláctico)
    - only_hits: si True, solo devuelve canciones que fueron hits
    """
    from sklearn.preprocessing import StandardScaler

    n = n or config.N_SIBLINGS
    pool = df.copy()

    # Filtrar por género si es intragaláctico
    if genre:
        genre_pool = pool[pool["track_genre"] == genre]
        if len(genre_pool) >= n:
            pool = genre_pool

    # Filtrar solo hits si se pide
    if only_hits:
        hits_pool = pool[pool["popularity"] >= config.HIT_THRESHOLD]
        if len(hits_pool) >= n:
            pool = hits_pool

    if len(pool) == 0:
        return []

    # Normalizar features para distancia justa
    scaler = StandardScaler()
    pool_scaled = scaler.fit_transform(pool[SIBLING_FEATURES])
    track_vec = scaler.transform(
        np.array([[track_features.get(f, 0) for f in SIBLING_FEATURES]])
    )

    # Distancia euclidiana
    distances = np.linalg.norm(pool_scaled - track_vec, axis=1)
    pool = pool.copy()
    pool["distance"] = distances

    # Similitud 0-100 (inversa de distancia normalizada)
    max_d = distances.max() if distances.max() > 0 else 1
    pool["similarity"] = (1 - pool["distance"] / max_d) * 100

    nearest = pool.nsmallest(n, "distance")

    siblings = []
    for _, row in nearest.iterrows():
        siblings.append({
            "id":         row.get("track_id", ""),
            "name":       row.get("track_name", ""),
            "artist":     row.get("artists", ""),
            "genre":      row.get("track_genre", ""),
            "popularity": int(row["popularity"]),
            "similarity": round(float(row["similarity"]), 1),
            "tempo":      round(float(row["tempo"]), 0),
            "danceability": round(float(row["danceability"]), 2),
            "valence":    round(float(row["valence"]), 2),
        })
    return siblings
