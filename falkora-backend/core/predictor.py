"""
╔══════════════════════════════════════════════════════════╗
║  FALKORA — Cargador de modelo y predictor                ║
╚══════════════════════════════════════════════════════════╝
"""
import pickle
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class FalkoraModel:
    """Carga el modelo campeón y hace predicciones."""

    def __init__(self):
        with open(config.MODEL_PATH, "rb") as f:
            self.model = pickle.load(f)
        with open(config.GENRE_ENCODER, "rb") as f:
            self.le_genre = pickle.load(f)
        with open(config.LABEL_ENCODER, "rb") as f:
            self.le_label = pickle.load(f)

        self.known_genres = list(self.le_genre.classes_)

    def predict(self, features: dict, genre: str = "latin") -> dict:
        """
        Predice hit/mid/flop para un set de features.
        """
        feats = dict(features)

        # Encodear género (si no se conoce, usar el más cercano)
        if genre not in self.known_genres:
            genre = "latin" if "latin" in self.known_genres else self.known_genres[0]
        feats["genre_encoded"] = int(self.le_genre.transform([genre])[0])

        # Construir vector en el orden correcto
        X = pd.DataFrame([feats])[config.FEATURES]

        pred_encoded = self.model.predict(X)[0]
        proba = self.model.predict_proba(X)[0]

        label = self.le_label.inverse_transform([pred_encoded])[0]
        proba_dict = {
            cls: round(float(p), 4)
            for cls, p in zip(self.le_label.classes_, proba)
        }

        # Hit Score 0-100 (probabilidad ponderada)
        hit_score = round(
            proba_dict.get("hit", 0) * 100 +
            proba_dict.get("mid", 0) * 50, 1
        )

        emoji = {"hit": "🌟", "mid": "✨", "flop": "💫"}

        return {
            "prediction":    label,
            "hit_score":     hit_score,
            "confidence":    round(float(max(proba)), 4),
            "probabilities": proba_dict,
            "emoji":         emoji.get(label, ""),
            "falkora_label": _falkora_label(label),
        }


def _falkora_label(label: str) -> str:
    """Traduce las clases a la narrativa Falkora."""
    return {
        "hit":  "Supernova",
        "mid":  "Rising Star",
        "flop": "Dormant Star"
    }.get(label, label)


# Singleton
_model_instance = None

def get_model() -> FalkoraModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = FalkoraModel()
    return _model_instance
