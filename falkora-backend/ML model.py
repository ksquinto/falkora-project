"""
╔══════════════════════════════════════════════════════════════════════╗
║              HIT SCORE LATAM — Pipeline Completo v6.1 LABEL V2 MEMORY SAFE               ║
║                                                                      ║
║  FLUJO:                                                              ║
║  1. Corre Modelo 1 (Solo Latino) → guarda en output/Modelo_1/        ║
║  2. Corre Modelo 2 (50/50)       → guarda en output/Modelo_2/        ║
║  3. Corre Modelo 3 (Completo)    → guarda en output/Modelo_3/        ║
║  4. Compara los 3 ganadores      → guarda en output/Campeon/         ║
║                                                                      ║
║  Cada carpeta contiene:                                              ║
║    eda.png, model_evaluation.png                                     ║
║    hit_score_model.pkl, genre_encoder.pkl, label_encoder.pkl         ║
║    model_metadata.json                                               ║
╚══════════════════════════════════════════════════════════════════════╝

REQUISITOS:
    pip install pandas numpy scikit-learn lightgbm xgboost matplotlib seaborn imbalanced-learn

USO:
    python ML_model_v6_1_memory_safe.py
"""

import os
import shutil
import gc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

import pandas as pd
import numpy as np
import seaborn as sns
import pickle
import json
import warnings
warnings.filterwarnings("ignore")

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.model_selection import (train_test_split, cross_val_score,
                                     GridSearchCV, StratifiedKFold)
from sklearn.metrics import (classification_report, confusion_matrix, f1_score)
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.base import clone
from imblearn.over_sampling import SMOTE
import lightgbm as lgb
import xgboost as xgb

# ═══════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════

DATA_PATH  = r"C:\Users\ksqr9\OneDrive\Falkora project\falkora-backend\data\dataset.csv"

# Carpeta separada para no mezclar con los modelos viejos.
OUTPUT_DIR = r"C:\Users\ksqr9\OneDrive\Falkora project\falkora-backend\output_label_v2\\"

LATIN_GENRES = [
    "latin", "latino", "mpb", "pagode", "reggae",
    "reggaeton", "salsa", "sertanejo", "tango"
]

GENRE_PRIORITY = [
    "reggaeton", "salsa", "latino", "latin",
    "reggae", "tango", "sertanejo", "pagode", "mpb"
]

GLOBAL_RELEVANT = [
    "dancehall", "afrobeat", "samba", "forro",
    "hip-hop", "r-n-b", "soul", "funk",
    "dance", "club", "party", "groove",
    "pop", "romance", "spanish", "disco", "house"
]

# Umbrales viejos: se conservan solo para auditoría.
OLD_HIT_THRESHOLD = 60
OLD_MID_THRESHOLD = 30

# Umbrales nuevos:
# El éxito se define por percentil dentro del contexto musical.
HIT_PERCENTILE = 0.80
MID_PERCENTILE = 0.40

# Si hay año, usa género + año solo cuando el grupo tiene suficientes canciones.
# Si no, usa fallback por género.
MIN_GROUP_SIZE_GENRE_YEAR = 30

COLORS = {"hit": "#1DB954", "mid": "#F59E0B", "flop": "#EF4444"}
ORDER  = ["hit", "mid", "flop"]
BG     = "#0F0F0F"
PANEL  = "#1A1A1A"

# OJO:
# popularity, popularity_score_v2, label_v2 NO entran como features.
# Solo sirven para construir el target.
FEATURES = [
    "danceability", "energy", "loudness", "speechiness",
    "acousticness", "instrumentalness", "liveness",
    "valence", "tempo", "explicit", "key", "mode",
    "time_signature", "genre_encoded", "duration_min"
]

RANDOM_STATE = 42

# ═══════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN MEMORY SAFE
# ═══════════════════════════════════════════════════════════════════
# Tu error venía de SMOTE + 5 folds + n_jobs=-1 + RandomForest grande.
# Esta versión prioriza que corra estable en Windows.
USE_SMOTE = False
RUN_TUNING = True
ENABLE_SVM = False

CV_SPLITS_BASELINE = 3
CV_SPLITS_TUNING = 3
CV_N_JOBS = 1
GRID_N_JOBS = 1

MAX_TUNING_ROWS = 60000
MAX_SVM_ROWS = 15000

DATE_COLUMN_CANDIDATES = [
    "release_date",
    "album_release_date",
    "track_album_release_date",
    "released_at",
    "release_year",
    "year",
]


# ═══════════════════════════════════════════════════════════════════
#  UTILIDADES
# ═══════════════════════════════════════════════════════════════════

def classify_old(popularity):
    """Label antiguo por popularity absoluta. Se conserva para auditoría."""
    if popularity >= OLD_HIT_THRESHOLD:
        return "hit"
    elif popularity >= OLD_MID_THRESHOLD:
        return "mid"
    else:
        return "flop"


def classify_v2(percentile_score):
    """Label nuevo por percentil contextual."""
    if pd.isna(percentile_score):
        return "flop"
    if percentile_score >= HIT_PERCENTILE:
        return "hit"
    elif percentile_score >= MID_PERCENTILE:
        return "mid"
    else:
        return "flop"


def make_folder(base, name):
    """Crea carpeta y retorna su path."""
    path = os.path.join(base, name, "")
    os.makedirs(path, exist_ok=True)
    return path


def extract_year_from_series(series):
    """
    Extrae año desde columnas tipo fecha o año.
    Soporta valores como:
    - 2024
    - "2024"
    - "2024-05-17"
    - "2024/05/17"
    """
    numeric = pd.to_numeric(series, errors="coerce")
    numeric_valid = numeric.where(numeric.between(1900, 2100))

    extracted = (
        series.astype(str)
        .str.extract(r"((?:19|20)\d{2})", expand=False)
    )
    extracted = pd.to_numeric(extracted, errors="coerce")
    extracted_valid = extracted.where(extracted.between(1900, 2100))

    return numeric_valid.fillna(extracted_valid)


def add_release_year(df):
    """
    Crea release_year si la base trae alguna columna de fecha/año.
    Si no trae año, queda en NaN y label_v2 usa fallback por género.
    """
    df = df.copy()

    year = pd.Series(np.nan, index=df.index, dtype="float64")
    for col in DATE_COLUMN_CANDIDATES:
        if col in df.columns:
            candidate_year = extract_year_from_series(df[col])
            year = year.fillna(candidate_year)

    df["release_year"] = year.astype("Int64")
    return df


def add_contextual_popularity_labels(df):
    """
    Construye el target label_v2:

    1. popularity_percentile_genre_year:
       ranking de popularity dentro de track_genre + release_year.

    2. popularity_percentile_genre:
       fallback por track_genre.

    3. popularity_percentile_global:
       fallback final.

    4. popularity_score_v2:
       score final contextual.

    5. label_v2:
       hit/mid/flop por percentiles:
       - hit  = top 20% de su contexto
       - mid  = entre 40% y 80%
       - flop = debajo de 40%
    """
    df = df.copy()

    if "popularity" not in df.columns:
        raise ValueError("El dataset debe tener una columna 'popularity'.")

    if "track_genre" not in df.columns:
        raise ValueError("El dataset debe tener una columna 'track_genre'.")

    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce")
    df = df.dropna(subset=["popularity", "track_genre"])

    df = add_release_year(df)

    # Label viejo para auditoría.
    df["label_old"] = df["popularity"].apply(classify_old)

    # Percentil global.
    df["popularity_percentile_global"] = df["popularity"].rank(
        pct=True,
        method="average"
    )

    # Percentil por género.
    df["popularity_percentile_genre"] = (
        df.groupby("track_genre")["popularity"]
        .rank(pct=True, method="average")
    )

    # Percentil por género + año, con protección por tamaño de grupo.
    df["popularity_percentile_genre_year"] = np.nan
    df["genre_year_group_size"] = np.nan

    has_year = df["release_year"].notna()
    if has_year.any():
        group_cols = ["track_genre", "release_year"]

        group_size = (
            df.loc[has_year]
            .groupby(group_cols)["popularity"]
            .transform("size")
        )

        group_rank = (
            df.loc[has_year]
            .groupby(group_cols)["popularity"]
            .rank(pct=True, method="average")
        )

        valid_genre_year = group_size >= MIN_GROUP_SIZE_GENRE_YEAR
        valid_index = df.loc[has_year].index[valid_genre_year]

        df.loc[has_year, "genre_year_group_size"] = group_size.values
        df.loc[valid_index, "popularity_percentile_genre_year"] = (
            group_rank[valid_genre_year].values
        )

    # Score final con fallback jerárquico.
    df["popularity_score_v2"] = df["popularity_percentile_genre_year"]
    df["label_score_source"] = np.where(
        df["popularity_score_v2"].notna(),
        "genre_year",
        ""
    )

    use_genre = df["popularity_score_v2"].isna() & df["popularity_percentile_genre"].notna()
    df.loc[use_genre, "popularity_score_v2"] = df.loc[use_genre, "popularity_percentile_genre"]
    df.loc[use_genre, "label_score_source"] = "genre"

    use_global = df["popularity_score_v2"].isna()
    df.loc[use_global, "popularity_score_v2"] = df.loc[use_global, "popularity_percentile_global"]
    df.loc[use_global, "label_score_source"] = "global"

    # Target final usado por el modelo.
    df["label_v2"] = df["popularity_score_v2"].apply(classify_v2)

    # Para no romper el resto del pipeline.
    df["label"] = df["label_v2"]

    return df


def print_label_audit(df):
    """Auditoría rápida del cambio label_old vs label_v2."""
    print("\n  🧪 Auditoría Label v2")
    print("  " + "─" * 50)

    source_counts = (
        df["label_score_source"]
        .value_counts(dropna=False)
        .rename_axis("source")
        .reset_index(name="tracks")
    )

    print("  Fuente del score contextual:")
    for _, row in source_counts.iterrows():
        pct = row["tracks"] / len(df) * 100
        print(f"    {row['source']:<12}: {row['tracks']:>7,} ({pct:>5.1f}%)")

    print("\n  Label antiguo vs Label v2:")
    audit = pd.crosstab(df["label_old"], df["label_v2"], margins=True)
    print(audit.to_string())

    print("\n  Distribución Label v2:")
    dist = df["label_v2"].value_counts().reindex(ORDER).fillna(0).astype(int)
    for label, n in dist.items():
        print(f"    {label:<5}: {n:>7,} ({n / len(df) * 100:>5.1f}%)")


def make_safe_cv(y, desired_splits, label):
    """
    Crea StratifiedKFold seguro.
    Si alguna clase tiene menos ejemplos que desired_splits, reduce folds.
    """
    class_counts = pd.Series(y).value_counts()
    min_count = int(class_counts.min())

    if min_count < 2:
        print(f"  ⚠️ {label}: no hay suficientes ejemplos por clase para CV. Se omite CV.")
        return None

    n_splits = min(desired_splits, min_count)
    n_splits = max(2, n_splits)

    if n_splits != desired_splits:
        print(f"  ⚠️ {label}: CV ajustado a {n_splits} folds por tamaño de clase.")

    return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)


def sample_for_tuning(X, y, max_rows=MAX_TUNING_ROWS):
    """
    Usa muestra estratificada para GridSearch.
    Luego el mejor modelo se reentrena con todo el train.
    """
    if len(X) <= max_rows:
        return X, y

    X_sample, _, y_sample, _ = train_test_split(
        X,
        y,
        train_size=max_rows,
        random_state=RANDOM_STATE,
        stratify=y
    )
    print(f"  ⚠️ Tuning con muestra estratificada: {len(X_sample):,} de {len(X):,} filas.")
    return X_sample, y_sample


def safe_cross_val_score(model, X, y, desired_splits, model_name):
    """
    Cross validation sin paralelismo agresivo.
    Si falla por memoria, no tumba el pipeline.
    """
    cv = make_safe_cv(y, desired_splits, f"CV {model_name}")
    if cv is None:
        return np.array([np.nan])

    try:
        return cross_val_score(
            model,
            X,
            y,
            cv=cv,
            scoring="f1_weighted",
            n_jobs=CV_N_JOBS,
            error_score=np.nan
        )
    except MemoryError:
        print(f"  ⚠️ {model_name}: CV omitido por memoria insuficiente.")
        return np.array([np.nan])
    except Exception as exc:
        print(f"  ⚠️ {model_name}: CV omitido por error: {exc}")
        return np.array([np.nan])


def feature_engineer(df):
    """
    Aplica feature engineering y retorna df + LabelEncoder de género.

    Cambio v6.1:
    - Antes: label = popularity absoluta.
    - Ahora: label = label_v2 basado en percentil contextual.
    """
    df = df.copy()

    required_cols = ["explicit", "duration_ms", "track_genre", "popularity"] + [
        c for c in FEATURES if c not in ["explicit", "duration_min", "genre_encoded"]
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el dataset: {missing}")

    df["explicit"] = df["explicit"].astype(int)
    df["duration_min"] = df["duration_ms"] / 60000

    le_genre = LabelEncoder()
    df["genre_encoded"] = le_genre.fit_transform(df["track_genre"].astype(str))

    df = add_contextual_popularity_labels(df)

    return df, le_genre


def dedup_latin(df):
    """Deduplica tracks latinos dando prioridad al género más específico."""
    df_latin = df[df["track_genre"].isin(LATIN_GENRES)].copy()
    df_latin["_priority"] = df_latin["track_genre"].map(
        {g: i for i, g in enumerate(GENRE_PRIORITY)}
    )
    df_latin = (df_latin
                .sort_values("_priority")
                .drop_duplicates(subset=["track_id"])
                .drop(columns=["_priority"]))
    return df_latin


# ═══════════════════════════════════════════════════════════════════
#  CARGA BASE
# ═══════════════════════════════════════════════════════════════════

def load_raw(path):
    print("─" * 60)
    print("  CARGANDO DATASET")
    print("─" * 60)
    df = pd.read_csv(path)
    print(f"  Original:         {df.shape[0]:,} filas × {df.shape[1]} columnas")
    antes = len(df)
    df = df.dropna(subset=["track_name", "album_name"])
    print(f"  Filas eliminadas: {antes - len(df)} (sin track/album)")
    year_cols = [c for c in DATE_COLUMN_CANDIDATES if c in df.columns]
    if year_cols:
        print(f"  Columnas de fecha/año detectadas: {year_cols}")
    else:
        print("  ⚠️ No detecté columna de año/fecha. Label v2 usará fallback por género.")

    print(f"  Dataset limpio:   {len(df):,} filas\n")
    return df


# ═══════════════════════════════════════════════════════════════════
#  CONSTRUCCIÓN DE DATASETS
# ═══════════════════════════════════════════════════════════════════

def build_dataset_1(df):
    """Solo tracks latinos con prioridad de género."""
    df_latin = dedup_latin(df)
    df_out, le_genre = feature_engineer(df_latin)
    print(f"  Tracks únicos: {len(df_out):,}")
    print(f"  Por género:")
    for g, n in df_out["track_genre"].value_counts().items():
        print(f"    {g:<15}: {n}")
    print_label_audit(df_out)
    return df_out, le_genre


def build_dataset_2(df):
    """50% latinos + 50% géneros globales afines."""
    df_latin = dedup_latin(df)

    df_global_pool = (
        df[df["track_genre"].isin(GLOBAL_RELEVANT)]
        .drop_duplicates(subset=["track_id"])
    )

    n_global = min(len(df_latin), len(df_global_pool))
    if n_global < len(df_latin):
        print(
            f"  ⚠️ Solo hay {n_global:,} tracks globales afines disponibles; "
            f"no se pudo hacer 50/50 exacto."
        )

    df_global = df_global_pool.sample(n=n_global, random_state=RANDOM_STATE)
    df_combined = pd.concat([df_latin, df_global], ignore_index=True)

    df_out, le_genre = feature_engineer(df_combined)
    print(f"  Latinos:  {len(df_latin):,}")
    print(f"  Globales: {len(df_global):,}")
    print(f"  Total:    {len(df_out):,}")
    print_label_audit(df_out)
    return df_out, le_genre


def build_dataset_3(df):
    """Todos los tracks del dataset."""
    df_all = df.drop_duplicates(subset=["track_id"]).copy()
    df_out, le_genre = feature_engineer(df_all)
    print(f"  Total tracks: {len(df_out):,}")
    print(f"  Géneros únicos: {df_out['track_genre'].nunique()}")
    print_label_audit(df_out)
    return df_out, le_genre


# ═══════════════════════════════════════════════════════════════════
#  EDA
# ═══════════════════════════════════════════════════════════════════

def run_eda(df, out_dir, titulo):
    title_kw = dict(color="white", fontsize=11, fontweight="bold", pad=10)
    label_kw = dict(color="#AAAAAA", fontsize=8)
    tick_kw  = dict(colors="#888888", labelsize=7)

    fig = plt.figure(figsize=(22, 28))
    fig.patch.set_facecolor(BG)
    gs  = gridspec.GridSpec(5, 3, figure=fig, hspace=0.55, wspace=0.35)

    # 1. Clases
    ax1 = fig.add_subplot(gs[0, 0])
    counts = df["label"].value_counts().reindex(ORDER)
    bars = ax1.bar(ORDER, counts.values,
                   color=[COLORS[l] for l in ORDER], width=0.55, edgecolor="none")
    for bar, val in zip(bars, counts.values):
        ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+15,
                 f"{val:,}\n({val/len(df)*100:.1f}%)",
                 ha="center", va="bottom", color="white", fontsize=8)
    ax1.set_facecolor(PANEL); ax1.set_title("Distribución de Clases — Label v2", **title_kw)
    ax1.set_ylabel("Tracks", **label_kw); ax1.tick_params(**tick_kw)
    ax1.spines[:].set_visible(False); ax1.set_ylim(0, counts.max()*1.25)

    # 2. Popularity Score v2
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.hist(df["popularity_score_v2"], bins=40, color="#1DB954", edgecolor="none", alpha=0.85)
    ax2.axvline(MID_PERCENTILE, color="#F59E0B", lw=1.5, ls="--", label=f"mid ({MID_PERCENTILE:.2f})")
    ax2.axvline(HIT_PERCENTILE, color="#EF4444", lw=1.5, ls="--", label=f"hit ({HIT_PERCENTILE:.2f})")
    ax2.set_facecolor(PANEL); ax2.set_title("Distribución Popularity Score v2", **title_kw)
    ax2.set_xlabel("Percentil contextual (0–1)", **label_kw); ax2.set_ylabel("Frecuencia", **label_kw)
    ax2.tick_params(**tick_kw)
    ax2.legend(fontsize=7, facecolor=PANEL, labelcolor="white", framealpha=0.5)
    ax2.spines[:].set_visible(False)

    # 3. Top géneros
    ax3 = fig.add_subplot(gs[0, 2])
    gc = df["track_genre"].value_counts().head(15)
    cg = plt.cm.Set2(np.linspace(0, 1, len(gc)))
    b3 = ax3.barh(gc.index, gc.values, color=cg, edgecolor="none")
    for bar, val in zip(b3, gc.values):
        ax3.text(val+5, bar.get_y()+bar.get_height()/2,
                 str(val), va="center", color="white", fontsize=7)
    ax3.set_facecolor(PANEL); ax3.set_title("Top 15 Géneros", **title_kw)
    ax3.set_xlabel("Tracks", **label_kw); ax3.tick_params(**tick_kw)
    ax3.spines[:].set_visible(False)

    # 4. Popularity promedio por género
    ax4 = fig.add_subplot(gs[1, 0])
    gp = df.groupby("track_genre")["popularity"].mean().sort_values().tail(15)
    c4 = ["#1DB954" if v>=40 else "#F59E0B" if v>=25 else "#EF4444" for v in gp.values]
    b4 = ax4.barh(gp.index, gp.values, color=c4, edgecolor="none")
    for bar, val in zip(b4, gp.values):
        ax4.text(val+0.3, bar.get_y()+bar.get_height()/2,
                 f"{val:.1f}", va="center", color="white", fontsize=7)
    ax4.set_facecolor(PANEL); ax4.set_title("Popularity Promedio por Género", **title_kw)
    ax4.set_xlabel("Popularity", **label_kw); ax4.tick_params(**tick_kw)
    ax4.spines[:].set_visible(False)

    # 5. Heatmap
    ax5 = fig.add_subplot(gs[1, 1:])
    nf = ["popularity","danceability","energy","loudness","speechiness",
          "acousticness","instrumentalness","liveness","valence","tempo","duration_min"]
    corr = df[nf].corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, ax=ax5, cmap="RdYlGn", center=0,
                annot=True, fmt=".2f", annot_kws={"size":6},
                linewidths=0.3, linecolor=BG, cbar_kws={"shrink":0.7})
    ax5.set_facecolor(PANEL); ax5.set_title("Matriz de Correlación", **title_kw)
    ax5.tick_params(**tick_kw)

    # 6-8. Boxplots
    for i, (feat, fname) in enumerate([
        ("danceability","Danceability"),("energy","Energy"),("valence","Valence")
    ]):
        ax = fig.add_subplot(gs[2, i])
        data = [df[df["label"]==l][feat].values for l in ORDER]
        bp = ax.boxplot(data, patch_artist=True,
                        medianprops=dict(color="white", linewidth=2),
                        whiskerprops=dict(color="#888888"),
                        capprops=dict(color="#888888"),
                        flierprops=dict(marker="o", markersize=2,
                                        markerfacecolor="#555555", linestyle="none"))
        for patch, label in zip(bp["boxes"], ORDER):
            patch.set_facecolor(COLORS[label]); patch.set_alpha(0.85)
        ax.set_xticklabels(ORDER, fontsize=8, color="white")
        ax.set_facecolor(PANEL); ax.set_title(fname, **title_kw)
        ax.set_ylabel("Valor", **label_kw); ax.tick_params(**tick_kw)
        ax.spines[:].set_visible(False)

    # 9. Tempo por género
    ax9 = fig.add_subplot(gs[3, 0])
    gt = df.groupby("track_genre")["tempo"].mean().sort_values().tail(10)
    c9 = plt.cm.plasma(np.linspace(0.2, 0.9, len(gt)))
    b9 = ax9.barh(gt.index, gt.values, color=c9, edgecolor="none")
    for bar, val in zip(b9, gt.values):
        ax9.text(val+0.5, bar.get_y()+bar.get_height()/2,
                 f"{val:.0f}", va="center", color="white", fontsize=7)
    ax9.set_facecolor(PANEL); ax9.set_title("Tempo Promedio por Género (BPM)", **title_kw)
    ax9.set_xlabel("BPM", **label_kw); ax9.tick_params(**tick_kw)
    ax9.spines[:].set_visible(False)

    # 10. % hits por género
    ax10 = fig.add_subplot(gs[3, 1])
    hr = (df[df["label"]=="hit"].groupby("track_genre").size() /
          df.groupby("track_genre").size() * 100).sort_values().tail(10).fillna(0)
    c10 = ["#1DB954" if v>=8 else "#F59E0B" if v>=4 else "#EF4444" for v in hr.values]
    b10 = ax10.barh(hr.index, hr.values, color=c10, edgecolor="none")
    for bar, val in zip(b10, hr.values):
        ax10.text(val+0.1, bar.get_y()+bar.get_height()/2,
                  f"{val:.1f}%", va="center", color="white", fontsize=7)
    ax10.set_facecolor(PANEL); ax10.set_title("% Hits por Género — Label v2", **title_kw)
    ax10.set_xlabel("% hits", **label_kw); ax10.tick_params(**tick_kw)
    ax10.spines[:].set_visible(False)

    # 11. Explicit
    ax11 = fig.add_subplot(gs[3, 2])
    ep = df.groupby("explicit")["popularity"].mean()
    b11 = ax11.bar(["No Explicit","Explicit"], ep.values,
                   color=["#1DB954","#EF4444"], width=0.5, edgecolor="none")
    for bar, val in zip(b11, ep.values):
        ax11.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
                  f"{val:.1f}", ha="center", va="bottom", color="white", fontsize=9)
    ax11.set_facecolor(PANEL); ax11.set_title("Explicit vs Popularity", **title_kw)
    ax11.set_ylabel("Popularity", **label_kw); ax11.tick_params(**tick_kw)
    ax11.spines[:].set_visible(False)

    # 12. Scatter
    ax12 = fig.add_subplot(gs[4, :2])
    for label in ORDER:
        sub = df[df["label"]==label]
        ax12.scatter(sub["danceability"], sub["energy"],
                     c=COLORS[label], label=label, alpha=0.3, s=10, edgecolors="none")
    ax12.set_facecolor(PANEL); ax12.set_title("Danceability vs Energy", **title_kw)
    ax12.set_xlabel("Danceability", **label_kw); ax12.set_ylabel("Energy", **label_kw)
    ax12.tick_params(**tick_kw); ax12.spines[:].set_visible(False)
    ax12.legend(fontsize=8, facecolor=PANEL, labelcolor="white", framealpha=0.5)

    # 13. Duración
    ax13 = fig.add_subplot(gs[4, 2])
    for label in ORDER:
        ax13.hist(df[df["label"]==label]["duration_min"], bins=25,
                  alpha=0.6, color=COLORS[label], label=label, edgecolor="none")
    ax13.set_facecolor(PANEL); ax13.set_title("Duración por Clase (min)", **title_kw)
    ax13.set_xlabel("Minutos", **label_kw); ax13.set_ylabel("Frecuencia", **label_kw)
    ax13.tick_params(**tick_kw); ax13.spines[:].set_visible(False)
    ax13.legend(fontsize=8, facecolor=PANEL, labelcolor="white", framealpha=0.5)

    fig.suptitle(f"HIT SCORE LATAM — EDA — {titulo} — LABEL V2",
                 color="white", fontsize=15, fontweight="bold", y=0.99)
    plt.savefig(f"{out_dir}eda.png", dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  ✅ eda.png guardado")


# ═══════════════════════════════════════════════════════════════════
#  PREPARAR DATOS
# ═══════════════════════════════════════════════════════════════════

def prepare_modeling_data(df):
    """
    Prepara X/y.
    Importante: popularity, popularity_score_v2 y label_v2 no entran en X.

    Versión memory safe:
    - SMOTE queda apagado por defecto.
    - label_v2 ya balancea mejor las clases por percentiles.
    - Si quieres reactivar SMOTE, cambia USE_SMOTE = True arriba.
    """
    X = df[FEATURES].copy()

    # Menos memoria: float32/int32 en vez de float64 cuando sea posible.
    for col in X.columns:
        if pd.api.types.is_float_dtype(X[col]):
            X[col] = X[col].astype("float32")
        elif pd.api.types.is_integer_dtype(X[col]):
            X[col] = X[col].astype("int32")

    le_label = LabelEncoder()
    y = le_label.fit_transform(df["label"])

    print("  Clases LabelEncoder:", dict(zip(le_label.classes_, range(len(le_label.classes_)))))

    X_train_raw, X_test, y_train_raw, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    if USE_SMOTE:
        class_counts = pd.Series(y_train_raw).value_counts()
        min_class_count = int(class_counts.min())
        if min_class_count <= 1:
            print("  ⚠️ Clase con 1 solo ejemplo. No se aplica SMOTE.")
            X_train, y_train = X_train_raw, y_train_raw
        else:
            k_neighbors = min(5, min_class_count - 1)
            smote = SMOTE(random_state=RANDOM_STATE, k_neighbors=k_neighbors)
            X_train, y_train = smote.fit_resample(X_train_raw, y_train_raw)
            print(f"  SMOTE aplicado con k_neighbors={k_neighbors}")
    else:
        X_train, y_train = X_train_raw, y_train_raw
        print("  SMOTE: NO aplicado. Label v2 ya genera clases por percentiles.")

    print(
        f"  Train original: {len(X_train_raw):,} | "
        f"Train final: {len(X_train):,} | Test: {len(X_test):,}"
    )

    return X_train, X_test, y_train, y_test, le_label


# ═══════════════════════════════════════════════════════════════════
#  COMPETENCIA DE MODELOS
# ═══════════════════════════════════════════════════════════════════

def run_model_competition(X_train, X_test, y_train, y_test, le_label):
    models = {
        "Random Forest": RandomForestClassifier(
            n_estimators=80,
            max_depth=12,
            min_samples_leaf=10,
            max_features="sqrt",
            random_state=RANDOM_STATE,
            n_jobs=1,
            class_weight="balanced_subsample"
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=120,
            learning_rate=0.08,
            max_depth=3,
            random_state=RANDOM_STATE
        ),
        "LightGBM": lgb.LGBMClassifier(
            n_estimators=150,
            learning_rate=0.08,
            num_leaves=31,
            max_depth=10,
            random_state=RANDOM_STATE,
            n_jobs=1,
            verbose=-1
        ),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=150,
            learning_rate=0.08,
            max_depth=4,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=RANDOM_STATE,
            eval_metric="mlogloss",
            tree_method="hist",
            n_jobs=1,
            verbosity=0
        ),
    }

    if ENABLE_SVM and len(X_train) <= MAX_SVM_ROWS:
        models["SVM"] = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", SVC(probability=True, random_state=RANDOM_STATE))
        ])
    elif ENABLE_SVM:
        print(f"  ⚠️ SVM omitido: train tiene {len(X_train):,} filas y MAX_SVM_ROWS={MAX_SVM_ROWS:,}.")

    results = {}

    for name, model in models.items():
        print(f"  🔄 {name}...")

        try:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            cv_f1 = safe_cross_val_score(
                clone(model),
                X_train,
                y_train,
                CV_SPLITS_BASELINE,
                name
            )

            test_f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

            results[name] = {
                "model": model,
                "y_pred": y_pred,
                "cv_f1": float(np.nanmean(cv_f1)),
                "cv_std": float(np.nanstd(cv_f1)),
                "test_f1": float(test_f1),
            }

            yl = le_label.inverse_transform(y_pred)
            yt = le_label.inverse_transform(y_test)
            print(
                f"     CV F1: {np.nanmean(cv_f1):.3f} ± {np.nanstd(cv_f1):.3f} | "
                f"Test F1: {test_f1:.3f}"
            )
            print(classification_report(yt, yl, digits=3, zero_division=0))

        except MemoryError:
            print(f"  ❌ {name} omitido por memoria insuficiente.")
        except Exception as exc:
            print(f"  ❌ {name} omitido por error: {exc}")

        gc.collect()

    if not results:
        raise RuntimeError("Ningún modelo pudo entrenar. Reduce el dataset o revisa memoria disponible.")

    return results


# ═══════════════════════════════════════════════════════════════════
#  TUNING
# ═══════════════════════════════════════════════════════════════════

def run_hyperparameter_tuning(X_train, y_train, results):
    if not RUN_TUNING:
        print("  ⚠️ Tuning desactivado por configuración RUN_TUNING=False.")
        for name in results:
            results[name]["tuned_model"] = results[name]["model"]
            results[name]["tuned_cv_f1"] = results[name]["cv_f1"]
            results[name]["best_params"] = {}
        return results

    cv = make_safe_cv(y_train, CV_SPLITS_TUNING, "GridSearch")
    if cv is None:
        print("  ⚠️ Tuning omitido: no hay suficientes ejemplos por clase.")
        for name in results:
            results[name]["tuned_model"] = results[name]["model"]
            results[name]["tuned_cv_f1"] = results[name]["cv_f1"]
            results[name]["best_params"] = {}
        return results

    X_tune, y_tune = sample_for_tuning(X_train, y_train, MAX_TUNING_ROWS)

    param_grids = {
        "Random Forest": {
            "model": RandomForestClassifier(
                random_state=RANDOM_STATE,
                n_jobs=1,
                class_weight="balanced_subsample"
            ),
            "params": {
                "n_estimators": [80, 120],
                "max_depth": [10, 14],
                "min_samples_leaf": [5, 10],
                "max_features": ["sqrt"],
            }
        },
        "LightGBM": {
            "model": lgb.LGBMClassifier(random_state=RANDOM_STATE, n_jobs=1, verbose=-1),
            "params": {
                "n_estimators": [100, 150],
                "learning_rate": [0.05, 0.1],
                "max_depth": [5, 10],
                "num_leaves": [31, 63],
            }
        },
        "XGBoost": {
            "model": xgb.XGBClassifier(
                random_state=RANDOM_STATE,
                eval_metric="mlogloss",
                tree_method="hist",
                n_jobs=1,
                verbosity=0
            ),
            "params": {
                "n_estimators": [100, 150],
                "learning_rate": [0.05, 0.1],
                "max_depth": [3, 5],
                "subsample": [0.8],
                "colsample_bytree": [0.9],
            }
        },
    }

    for name, cfg in param_grids.items():
        if name not in results:
            continue

        print(f"  🔧 Tuning {name}...")

        try:
            gs = GridSearchCV(
                cfg["model"],
                cfg["params"],
                cv=cv,
                scoring="f1_weighted",
                n_jobs=GRID_N_JOBS,
                verbose=0,
                error_score=np.nan
            )

            gs.fit(X_tune, y_tune)

            best_estimator = gs.best_estimator_

            # Reentrena el ganador con todo el train, no solo la muestra de tuning.
            best_estimator.fit(X_train, y_train)

            results[name]["tuned_model"] = best_estimator
            results[name]["tuned_cv_f1"] = float(gs.best_score_)
            results[name]["best_params"] = gs.best_params_

            print(f"     CV F1: {gs.best_score_:.3f} | Params: {gs.best_params_}")

        except MemoryError:
            print(f"  ⚠️ Tuning {name} omitido por memoria. Se usa modelo baseline.")
            results[name]["tuned_model"] = results[name]["model"]
            results[name]["tuned_cv_f1"] = results[name]["cv_f1"]
            results[name]["best_params"] = {}
        except Exception as exc:
            print(f"  ⚠️ Tuning {name} omitido por error: {exc}. Se usa modelo baseline.")
            results[name]["tuned_model"] = results[name]["model"]
            results[name]["tuned_cv_f1"] = results[name]["cv_f1"]
            results[name]["best_params"] = {}

        gc.collect()

    # Los modelos sin tuning explícito quedan con baseline.
    for name in results:
        if "tuned_model" not in results[name]:
            results[name]["tuned_model"] = results[name]["model"]
            results[name]["tuned_cv_f1"] = results[name]["cv_f1"]
            results[name]["best_params"] = {}

    return results


# ═══════════════════════════════════════════════════════════════════
#  EVALUACIÓN FINAL
# ═══════════════════════════════════════════════════════════════════

def evaluate_and_select(X_test, y_test, le_label, results, out_dir, titulo):
    # Evaluar modelos tuneados
    for name, res in results.items():
        model  = res.get("tuned_model", res["model"])
        y_pred = model.predict(X_test)
        res["final_y_pred"]  = y_pred
        res["final_test_f1"] = f1_score(y_test, y_pred, average="weighted")
        res["final_model"]   = model

    # Tabla
    print(f"\n  {'Algoritmo':<22} {'CV F1 base':>10} {'CV F1 tuned':>12} {'Test F1':>9}")
    print(f"  {'─'*22} {'─'*10} {'─'*12} {'─'*9}")
    best_name = max(results, key=lambda k: results[k].get("final_test_f1", 0))
    for name, res in results.items():
        base  = res.get("cv_f1", 0)
        tuned = res.get("tuned_cv_f1", base)
        test  = res.get("final_test_f1", 0)
        marca = " ✅" if name == best_name else ""
        print(f"  {name:<22} {base:>10.3f} {tuned:>12.3f} {test:>9.3f}{marca}")

    best        = results[best_name]
    best_model  = best["final_model"]
    y_pred_best = best["final_y_pred"]
    yt = le_label.inverse_transform(y_test)
    yp = le_label.inverse_transform(y_pred_best)

    print(f"\n  🏆 GANADOR: {best_name} — Test F1: {best['final_test_f1']:.3f}")
    print(classification_report(yt, yp, digits=3, zero_division=0))

    # ── Gráfico model_evaluation.png ─────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    fig.patch.set_facecolor(BG)

    # Bar baseline vs tuned
    ax = axes[0]; ax.set_facecolor(PANEL)
    names     = list(results.keys())
    base_f1s  = [results[n].get("cv_f1", 0) for n in names]
    tuned_f1s = [results[n].get("tuned_cv_f1", results[n].get("cv_f1",0)) for n in names]
    x = np.arange(len(names)); w = 0.35
    ax.bar(x-w/2, base_f1s,  w, label="Baseline", color="#3B82F6", alpha=0.8)
    ax.bar(x+w/2, tuned_f1s, w, label="Tuned",    color="#1DB954", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=25, ha="right", color="white", fontsize=8)
    ax.set_ylabel("F1 Weighted (CV)", color="#AAAAAA", fontsize=9)
    ax.set_title("Baseline vs Tuned — CV F1", color="white", fontsize=11, fontweight="bold")
    ax.legend(fontsize=8, facecolor=PANEL, labelcolor="white")
    ax.tick_params(colors="#888888"); ax.spines[:].set_visible(False); ax.set_ylim(0, 1.05)
    for xi, (b, t) in enumerate(zip(base_f1s, tuned_f1s)):
        ax.text(xi-w/2, b+0.01, f"{b:.3f}", ha="center", color="white", fontsize=7)
        ax.text(xi+w/2, t+0.01, f"{t:.3f}", ha="center", color="white", fontsize=7)

    # Confusion matrix
    ax2 = axes[1]; ax2.set_facecolor(PANEL)
    cm = confusion_matrix(yt, yp, labels=ORDER)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Greens",
                xticklabels=ORDER, yticklabels=ORDER,
                ax=ax2, cbar=False, annot_kws={"size":11,"color":"white"})
    ax2.set_title(f"Confusion Matrix — {best_name}",
                  color="white", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Predicho", color="#AAAAAA", fontsize=9)
    ax2.set_ylabel("Real",     color="#AAAAAA", fontsize=9)
    ax2.tick_params(colors="white", labelsize=9)

    # Feature importance
    ax3 = axes[2]; ax3.set_facecolor(PANEL)
    bm = best.get("tuned_model", best["model"])
    if hasattr(bm, "feature_importances_"):
        imp = pd.Series(bm.feature_importances_,
                        index=FEATURES).sort_values(ascending=True).tail(12)
        ci = plt.cm.RdYlGn(np.linspace(0.2, 0.9, len(imp)))
        ax3.barh(imp.index, imp.values, color=ci, edgecolor="none")
        for i, (feat, val) in enumerate(imp.items()):
            ax3.text(val+0.002, i, f"{val:.3f}", va="center", color="white", fontsize=7)
        ax3.set_title(f"Feature Importance — {best_name}",
                      color="white", fontsize=11, fontweight="bold")
        ax3.set_xlabel("Importancia", color="#AAAAAA", fontsize=9)
        ax3.tick_params(colors="white", labelsize=8); ax3.spines[:].set_visible(False)
    else:
        ax3.text(0.5, 0.5, "Feature importance\nno disponible",
                 ha="center", va="center", color="white", fontsize=10,
                 transform=ax3.transAxes)

    plt.suptitle(f"HIT SCORE LATAM — Evaluación — {titulo}",
                 color="white", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{out_dir}model_evaluation.png", dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  ✅ model_evaluation.png guardado")

    return best_name, best_model


# ═══════════════════════════════════════════════════════════════════
#  GUARDAR MODELO
# ═══════════════════════════════════════════════════════════════════

def save_label_audit(df, out_dir):
    """Guarda CSV con auditoría de labels para revisar cambios canción por canción."""
    cols = [
        "track_id", "track_name", "artists", "album_name", "track_genre",
        "release_year", "popularity",
        "popularity_percentile_genre_year", "popularity_percentile_genre",
        "popularity_percentile_global", "popularity_score_v2",
        "label_score_source", "label_old", "label_v2"
    ]
    cols = [c for c in cols if c in df.columns]
    df[cols].to_csv(os.path.join(out_dir, "label_audit_v2.csv"), index=False, encoding="utf-8-sig")
    print("  ✅ label_audit_v2.csv guardado")


def save_model(model, le_genre, le_label, best_name, results, out_dir, titulo, df_model):
    with open(f"{out_dir}hit_score_model.pkl", "wb") as f:
        pickle.dump(model, f)
    with open(f"{out_dir}genre_encoder.pkl", "wb") as f:
        pickle.dump(le_genre, f)
    with open(f"{out_dir}label_encoder.pkl", "wb") as f:
        pickle.dump(le_label, f)

    label_distribution = (
        df_model["label_v2"]
        .value_counts()
        .reindex(ORDER)
        .fillna(0)
        .astype(int)
        .to_dict()
    )

    source_distribution = (
        df_model["label_score_source"]
        .value_counts()
        .to_dict()
    )

    metadata = {
        "modelo": titulo,
        "algoritmo": best_name,
        "features": FEATURES,
        "classes": list(le_label.classes_),
        "target": "label_v2",
        "target_description": "hit/mid/flop creado con percentil contextual de popularity",
        "important_note": "popularity y popularity_score_v2 NO se usan como features; solo construyen el target.",
        "label_v2_thresholds": {
            "hit": f"popularity_score_v2 >= {HIT_PERCENTILE}",
            "mid": f"{MID_PERCENTILE} <= popularity_score_v2 < {HIT_PERCENTILE}",
            "flop": f"popularity_score_v2 < {MID_PERCENTILE}"
        },
        "fallback_logic": {
            "primary": "popularity_percentile_genre_year",
            "fallback_1": "popularity_percentile_genre",
            "fallback_2": "popularity_percentile_global",
            "min_group_size_genre_year": MIN_GROUP_SIZE_GENRE_YEAR
        },
        "old_label_thresholds_for_audit_only": {
            "hit": f"popularity >= {OLD_HIT_THRESHOLD}",
            "mid": f"{OLD_MID_THRESHOLD} <= popularity < {OLD_HIT_THRESHOLD}",
            "flop": f"popularity < {OLD_MID_THRESHOLD}"
        },
        "label_distribution": label_distribution,
        "score_source_distribution": source_distribution,
        "test_f1_weighted": round(results[best_name].get("final_test_f1", 0), 4),
        "best_params": results[best_name].get("best_params", {}),
        "smote_applied": USE_SMOTE,
        "memory_safe": {
            "cv_splits_baseline": CV_SPLITS_BASELINE,
            "cv_splits_tuning": CV_SPLITS_TUNING,
            "cv_n_jobs": CV_N_JOBS,
            "grid_n_jobs": GRID_N_JOBS,
            "max_tuning_rows": MAX_TUNING_ROWS,
            "enable_svm": ENABLE_SVM
        },
        "version": "6.1-label-v2-memory-safe"
    }

    with open(f"{out_dir}model_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    save_label_audit(df_model, out_dir)
    print(f"  ✅ Archivos guardados en {out_dir}")


# ═══════════════════════════════════════════════════════════════════
#  PIPELINE COMPLETO POR MODELO
# ═══════════════════════════════════════════════════════════════════

def run_pipeline(df_raw, build_fn, titulo, out_dir):
    print(f"\n{'═'*60}")
    print(f"  {titulo.upper()}")
    print(f"{'═'*60}\n")

    # Construir dataset
    df_model, le_genre = build_fn(df_raw)

    # EDA
    print("\n  📊 Generando EDA...")
    run_eda(df_model, out_dir, titulo)

    # Preparar datos
    print("\n  🔧 Preparando datos para modelado...")
    X_train, X_test, y_train, y_test, le_label = prepare_modeling_data(df_model)

    # Competencia baseline
    print("\n  🏁 Competencia de modelos (baseline)...")
    results = run_model_competition(X_train, X_test, y_train, y_test, le_label)

    # Tuning
    print("\n  🔧 Tuning de hiperparámetros...")
    results = run_hyperparameter_tuning(X_train, y_train, results)

    # Evaluación
    print("\n  📈 Evaluación final...")
    best_algo, best_model = evaluate_and_select(
        X_test, y_test, le_label, results, out_dir, titulo
    )

    # Guardar
    print("\n  💾 Guardando modelo...")
    save_model(best_model, le_genre, le_label, best_algo, results, out_dir, titulo, df_model)

    best_f1 = results[best_algo].get("final_test_f1", 0)
    print(f"\n  ✅ {titulo} completado — {best_algo} — F1: {best_f1:.3f}")

    return {
        "titulo":      titulo,
        "algoritmo":   best_algo,
        "test_f1":     best_f1,
        "out_dir":     out_dir,
        "model":       best_model,
        "le_genre":    le_genre,
        "le_label":    le_label,
        "results":     results,
    }


# ═══════════════════════════════════════════════════════════════════
#  CAMPEÓN FINAL — CARPETA 4
# ═══════════════════════════════════════════════════════════════════

def crown_champion(semifinalistas, output_dir):
    print(f"\n{'═'*60}")
    print(f"  FINAL — COMPITIENDO LOS 3 GANADORES")
    print(f"{'═'*60}\n")

    print(f"  {'Modelo':<35} {'Algoritmo':<22} {'Test F1':>8}")
    print(f"  {'─'*35} {'─'*22} {'─'*8}")
    for s in semifinalistas:
        print(f"  {s['titulo']:<35} {s['algoritmo']:<22} {s['test_f1']:>8.3f}")

    # El campeón es el de mayor Test F1
    campeon = max(semifinalistas, key=lambda x: x["test_f1"])

    print(f"\n  🏆 CAMPEÓN: {campeon['titulo']}")
    print(f"     Algoritmo: {campeon['algoritmo']}")
    print(f"     Test F1:   {campeon['test_f1']:.3f}")

    # Crear carpeta Campeon
    campeon_dir = make_folder(output_dir, "Campeon")

    # Copiar todos los archivos del ganador
    archivos = ["eda.png", "model_evaluation.png",
                "hit_score_model.pkl", "genre_encoder.pkl",
                "label_encoder.pkl", "label_audit_v2.csv",
                "model_metadata.json"]
    for archivo in archivos:
        src = os.path.join(campeon["out_dir"], archivo)
        dst = os.path.join(campeon_dir, archivo)
        if os.path.exists(src):
            shutil.copy2(src, dst)

    # Actualizar metadata del campeón
    with open(f"{campeon_dir}model_metadata.json", "r") as f:
        meta = json.load(f)
    meta["campeon"] = True
    meta["vs_modelos"] = [
        {"modelo": s["titulo"], "algoritmo": s["algoritmo"], "test_f1": s["test_f1"]}
        for s in semifinalistas
    ]
    with open(f"{campeon_dir}model_metadata.json", "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    # Gráfico comparativo final
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)

    nombres   = [s["titulo"].replace(" - "," -\n") for s in semifinalistas]
    f1_scores = [s["test_f1"] for s in semifinalistas]
    algoritmos = [s["algoritmo"] for s in semifinalistas]
    col_bars  = ["#1DB954" if s["titulo"]==campeon["titulo"] else "#3B82F6"
                 for s in semifinalistas]

    bars = ax.bar(range(len(nombres)), f1_scores,
                  color=col_bars, width=0.5, edgecolor="none")
    ax.set_xticks(range(len(nombres)))
    ax.set_xticklabels(nombres, color="white", fontsize=9)

    for bar, val, alg in zip(bars, f1_scores, algoritmos):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.005,
                f"{val:.3f}\n({alg})", ha="center", va="bottom",
                color="white", fontsize=9, fontweight="bold")

    ax.set_ylabel("Test F1 (weighted)", color="#AAAAAA", fontsize=10)
    ax.set_title("🏆 Comparativo Final — 3 Estrategias de Datos",
                 color="white", fontsize=13, fontweight="bold")
    ax.tick_params(colors="white", labelsize=9)
    ax.spines[:].set_visible(False); ax.set_ylim(0, 1.1)

    # Leyenda
    ax.text(0.98, 0.05, "🟢 Campeón  🔵 Semifinalista",
            transform=ax.transAxes, ha="right", va="bottom",
            color="#AAAAAA", fontsize=8)

    plt.tight_layout()
    plt.savefig(f"{campeon_dir}model_evaluation.png",
                dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"\n  ✅ Carpeta Campeón creada → {campeon_dir}")

    return campeon


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\n" + "═"*60)
    print("  HIT SCORE LATAM — Pipeline Completo v6.1 LABEL V2 MEMORY SAFE")
    print("  3 Modelos → Competencia → Campeón Final")
    print("  Target: label_v2 = éxito relativo por género/año o fallback por género")
    print("  Memory safe: SMOTE apagado, CV=3, n_jobs=1")
    print("═"*60)

    # Cargar base una sola vez
    df_raw = load_raw(DATA_PATH)

    # Definir los 3 modelos con sus carpetas
    modelos = [
        ("Modelo 1 - Solo Latino",         build_dataset_1, "Modelo_1_Solo_Latino"),
        ("Modelo 2 - Latino Global 50/50", build_dataset_2, "Modelo_2_Latino_Global"),
        ("Modelo 3 - Dataset Completo",    build_dataset_3, "Modelo_3_Completo"),
    ]

    semifinalistas = []

    # Correr cada modelo
    for titulo, build_fn, folder_name in modelos:
        out_dir = make_folder(OUTPUT_DIR, folder_name)
        resultado = run_pipeline(df_raw, build_fn, titulo, out_dir)
        semifinalistas.append(resultado)

    # Elegir campeón y crear carpeta 4
    campeon = crown_champion(semifinalistas, OUTPUT_DIR)

    # Resumen final
    print(f"\n{'═'*60}")
    print(f"  ✅ PIPELINE COMPLETO — v6.1 LABEL V2 MEMORY SAFE")
    print(f"  📁 Carpetas generadas en: {OUTPUT_DIR}")
    print(f"     ├── Modelo_1_Solo_Latino/")
    print(f"     ├── Modelo_2_Latino_Global/")
    print(f"     ├── Modelo_3_Completo/")
    print(f"     └── Campeon/  ← {campeon['titulo']}")
    print(f"\n  🏆 CAMPEÓN FINAL: {campeon['titulo']}")
    print(f"     Algoritmo:     {campeon['algoritmo']}")
    print(f"     Test F1:       {campeon['test_f1']:.3f}")
    print(f"{'═'*60}\n")
