"""
╔══════════════════════════════════════════════════════════╗
║  FALKORA — Extractor de Audio (Essentia vía WSL2)        ║
║                                                          ║
║  Convierte un WAV en features llamando a Ubuntu/Essentia ║
║  desde Windows automáticamente.                          ║
╚══════════════════════════════════════════════════════════╝
"""
import subprocess
import json
import os
import sys


def extract_features(audio_path: str) -> dict:
    """
    Extrae features de un WAV llamando a Essentia en Ubuntu WSL2.
    
    Flujo:
    1. Windows recibe el WAV
    2. Llama al script Python en Ubuntu vía WSL
    3. Ubuntu/Essentia procesa y devuelve JSON
    4. Windows parsea y devuelve
    """
    
    # Convertir ruta de Windows a formato WSL
    # C:\Users\... → /mnt/c/Users/...
    wsl_path = audio_path.replace("\\", "/").replace("C:", "/mnt/c").replace("c:", "/mnt/c")
    
    # Comando para ejecutar en WSL
    cmd = [
        "wsl",
        "~/falkora-essentia/venv/bin/python",
        "~/falkora-essentia/extract_single_wav.py",
        wsl_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 60 segundos máximo
        )
        
        if result.returncode != 0:
            return {
                "error": f"Essentia extraction failed: {result.stderr}",
                "success": False
            }
        
        # Parsear JSON de salida
        data = json.loads(result.stdout)
        
        if not data.get("success"):
            return data
        
        return data["features"]
        
    except subprocess.TimeoutExpired:
        return {"error": "Extraction timeout (>60s)", "success": False}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON from Essentia: {e}", "success": False}
    except Exception as e:
        return {"error": f"Extraction error: {str(e)}", "success": False}


def extract_features_librosa(audio_path: str) -> dict:
    """
    Fallback con librosa si WSL/Essentia falla.
    Menos preciso pero funciona en cualquier entorno.
    """
    try:
        import librosa
        import numpy as np
    except ImportError:
        return {"error": "librosa not installed", "success": False}

    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        duration_sec = len(y) / sr

        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        rms = float(np.mean(librosa.feature.rms(y=y)))
        centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))

        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        key = int(np.argmax(np.mean(chroma, axis=1)))

        energy = float(np.clip(rms * 10, 0, 1))
        acousticness = float(np.clip(1 - centroid / sr, 0, 1))
        speechiness = float(np.clip(zcr * 2, 0, 1))

        return {
            "danceability": round(float(np.clip(tempo / 180, 0, 1)), 4),
            "energy": round(energy, 4),
            "loudness": round(20 * np.log10(rms + 1e-9), 2),
            "speechiness": round(speechiness, 4),
            "acousticness": round(acousticness, 4),
            "instrumentalness": round(float(np.clip(1 - speechiness * 1.5, 0, 1)), 4),
            "liveness": 0.15,
            "valence": round(float(np.clip(tempo / 200 + 0.3, 0, 1)), 4),
            "tempo": round(float(tempo), 2),
            "key": key,
            "mode": 1,
            "time_signature": 4,
            "duration_min": round(duration_sec / 60, 2),
            "explicit": 0,
            "_method": "librosa_fallback"
        }
    except Exception as e:
        return {"error": f"librosa extraction failed: {str(e)}", "success": False}
