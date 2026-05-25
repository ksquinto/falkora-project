"""
╔══════════════════════════════════════════════════════════╗
║  FALKORA — Diagnóstico (Gravity Score + Brechas)         ║
║                                                          ║
║  El corazón del producto: compara tu track contra los    ║
║  hits, en modo intragaláctico (tu género) o              ║
║  extragaláctico (todos), y explica qué mejorar.          ║
╚══════════════════════════════════════════════════════════╝
"""
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def get_reference_hits(df: pd.DataFrame, genre: str, mode: str) -> pd.DataFrame:
    """
    Devuelve el conjunto de hits de referencia según el modo.

    - intragalactic: solo hits del MISMO género (top percentil de su género)
    - extragalactic: todos los hits del universo
    """
    if mode == "intragalactic":
        genre_df = df[df["track_genre"] == genre]
        if len(genre_df) < 10:
            # Si hay muy pocos del género, ampliar a todos
            genre_df = df
        threshold = np.percentile(genre_df["popularity"], config.SUPERNOVA_PERCENTILE)
        return genre_df[genre_df["popularity"] >= threshold]
    else:
        return df[df["popularity"] >= config.HIT_THRESHOLD]


def compute_gaps(track_features: dict, reference_hits: pd.DataFrame) -> list:
    """
    Calcula las brechas entre tu track y el ADN promedio de los hits.
    """
    gaps = []
    for feat in config.DIAGNOSIS_FEATURES:
        yours  = track_features.get(feat, 0)
        target = float(reference_hits[feat].mean())
        delta  = yours - target

        if abs(delta) < 0.08:
            status = "ok"
        elif delta < 0:
            status = "below"
        else:
            status = "above"

        gaps.append({
            "feature": feat,
            "yours":   round(float(yours), 3),
            "target":  round(target, 3),
            "delta":   round(float(delta), 3),
            "status":  status,
        })
    return gaps


def compute_gravity_score(track_features: dict, reference_hits: pd.DataFrame) -> float:
    """
    Gravity Score: qué tanto 'atrae' tu track hacia el cúmulo de hits.
    Basado en distancia euclidiana inversa al centroide de hits.
    100 = idéntico al hit promedio, 0 = muy lejos.
    """
    from sklearn.preprocessing import minmax_scale

    centroid = reference_hits[config.DIAGNOSIS_FEATURES].mean().values
    yours    = np.array([track_features.get(f, 0) for f in config.DIAGNOSIS_FEATURES])

    distance = np.linalg.norm(yours - centroid)
    max_dist = np.sqrt(len(config.DIAGNOSIS_FEATURES))  # distancia máxima teórica

    gravity = max(0, (1 - distance / max_dist)) * 100
    return round(gravity, 1)


def generate_explanation(gaps: list, gravity: float, genre: str, mode: str) -> str:
    """
    Genera explicación en lenguaje natural (placeholder para LLM).
    En producción esto llamaría a la API de Claude para texto experto.
    """
    scope = f"las {genre}s que funcionaron" if mode == "intragalactic" else "los hits del universo musical"

    # Identificar las 2 brechas más grandes
    sorted_gaps = sorted(gaps, key=lambda g: abs(g["delta"]), reverse=True)
    worst = [g for g in sorted_gaps if g["status"] != "ok"][:2]

    if not worst:
        return (f"Tu track tiene un Gravity Score de {gravity}/100 — está muy alineado "
                f"con {scope}. Las características son sólidas en todos los ejes.")

    parts = [f"Tu track tiene un Gravity Score de {gravity}/100 comparado con {scope}."]
    for g in worst:
        direction = "por debajo" if g["status"] == "below" else "por encima"
        parts.append(
            f"Tu {g['feature']} ({g['yours']}) está {abs(g['delta']):.2f} {direction} "
            f"del promedio de hits ({g['target']})."
        )

    # Recomendación
    recs = []
    for g in worst:
        if g["feature"] == "valence" and g["status"] == "below":
            recs.append("trabaja una progresión armónica más luminosa y festiva")
        elif g["feature"] == "danceability" and g["status"] == "below":
            recs.append("refuerza el groove rítmico y la marcación del beat")
        elif g["feature"] == "energy" and g["status"] == "below":
            recs.append("sube la intensidad en el drop y los coros")
        elif g["feature"] == "acousticness" and g["status"] == "above":
            recs.append("agrega más producción electrónica y menos elementos acústicos")
    if recs:
        parts.append("Recomendación: " + ", ".join(recs) + ".")

    return " ".join(parts)


def diagnose(track_features: dict, df: pd.DataFrame, genre: str, mode: str) -> dict:
    """
    Diagnóstico completo: brechas + gravity score + explicación.
    """
    reference = get_reference_hits(df, genre, mode)
    gaps      = compute_gaps(track_features, reference)
    gravity   = compute_gravity_score(track_features, reference)
    text      = generate_explanation(gaps, gravity, genre, mode)

    return {
        "mode":          mode,
        "genre":         genre,
        "gravity_score": gravity,
        "reference_n":   len(reference),
        "gaps":          gaps,
        "explanation":   text,
        "radar": {
            "axes":   [g["feature"] for g in gaps],
            "yours":  [g["yours"]  for g in gaps],
            "target": [g["target"] for g in gaps],
        }
    }
