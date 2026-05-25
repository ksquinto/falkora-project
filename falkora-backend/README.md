# 🌌 Falkora — Backend API

> *"Where music becomes stars."*

Backend FastAPI que predice el potencial de hit de canciones latinas y las ubica en la galaxia Falkora.

---

## Conceptos

| Término | Significado |
|---|---|
| **Supernova** | Hit explosivo (top de su categoría) |
| **Rising Star** | Canción con potencial creciente |
| **Dormant Star** | Track con poca resonancia |
| **Gravity Score** | Qué tanto se acerca tu track al cúmulo de hits (0-100) |
| **Orbit Mapping** | Visualización 2D/3D de cercanía musical (UMAP) |
| **Stellar Siblings** | Las canciones-hit más parecidas a la tuya |

---

## Modo Intra vs Extragaláctico

El éxito es **relativo al género**. Una salsa no compite contra reggaetón.

- **🪐 Intragaláctico** — tu track vs solo los hits de su género. Una salsa es Supernova si está en el top 10% de *las salsas*.
- **🌍 Extragaláctico** — tu track vs todo el universo musical. Umbral absoluto de popularidad.

El frontend cambia entre modos con un toggle en vivo — todo se recalcula.

---

## Estructura

```
falkora-backend/
├── main.py              # FastAPI + endpoints
├── config.py            # Configuración central
├── core/
│   ├── predictor.py     # Carga modelo .pkl y predice
│   ├── audio_extractor.py # WAV → features (Essentia)
│   ├── galaxy.py        # UMAP → coordenadas de estrellas
│   ├── diagnosis.py     # Brechas + Gravity Score
│   └── siblings.py      # Hermanos sonoros
├── data/
│   └── dataset.csv      # ← copia aquí tu dataset
└── models/
    ├── hit_score_model.pkl   # ← copia aquí del Campeón
    ├── genre_encoder.pkl
    └── label_encoder.pkl
```

---

## Setup

### 1. Copia tus archivos
```
data/dataset.csv          ← tu dataset de Kaggle
models/hit_score_model.pkl ← de output/Campeon/
models/genre_encoder.pkl
models/label_encoder.pkl
```

### Opción A — Docker (recomendada, incluye Essentia)
```bash
docker build -t falkora-backend .
docker run -p 8000:8000 falkora-backend
```

### Opción B — Local sin Essentia (usa librosa)
```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

---

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET`  | `/` | Estado de la API |
| `POST` | `/analyze` | Análisis completo desde features |
| `POST` | `/analyze/upload` | Sube WAV → extrae → analiza |
| `GET`  | `/galaxy?mode=...` | Mapa completo de estrellas |
| `GET`  | `/genres` | Géneros disponibles |
| `GET`  | `/health` | Health check |

### Docs interactivas
```
http://localhost:8000/docs
```

---

## Ejemplo de uso

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "danceability": 0.62, "energy": 0.81, "loudness": -5.2,
      "speechiness": 0.08, "acousticness": 0.22, "instrumentalness": 0.0,
      "liveness": 0.12, "valence": 0.45, "tempo": 94,
      "key": 9, "mode": 0, "duration_min": 3.8, "genre": "salsa"
    },
    "mode": "intragalactic"
  }'
```

Respuesta: veredicto (Supernova/Rising/Dormant) + Gravity Score + brechas + hermanos sonoros + posición en galaxia.

---

## Próximo paso

El frontend en React + Three.js que consume estos endpoints y renderiza la galaxia navegable.
