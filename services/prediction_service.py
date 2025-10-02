# prediction_service.py
# Travel-time prediction service using Pandas + scikit-learn.
# - Trains models from historical records in SQLite
# - One model per OD pair; falls back to a global model
# - Features: hour, day_of_week, weather, traffic_level

from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List
import pandas as pd
import numpy as np

# ML
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error

# ----------------------------
# Configuration
# ----------------------------
DEFAULT_DB_PATH = "traffic_data.db"
TARGET_COLUMN = "travel_time_min"

# These are the input feature columns we expect in the DB
NUMERIC_COLS = ["distance_km", "avg_speed_kmph", "hour", "day_of_week"]
CATEGORICAL_COLS = ["weather", "traffic_level"]  # ex: "Clear/Rain/Cloudy", "Low/Medium/High"

REQUIRED_COLS = NUMERIC_COLS + CATEGORICAL_COLS + ["origin", "destination", TARGET_COLUMN, "timestamp"]

# ----------------------------
# Data structures
# ----------------------------
@dataclass
class TrainedModel:
    od_key: Optional[Tuple[str, str]]  # None means "global"
    pipeline: Pipeline
    metrics: Dict[str, float]

# ----------------------------
# Service
# ----------------------------
class PredictionService:
    """
    Trains and serves travel-time predictors using historical rows from SQLite.
    Each OD pair (origin, destination) gets a model if enough rows are available.
    Otherwise, we train one global model from all data.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH, min_rows_for_od_model: int = 60) -> None:
        self.db_path = db_path
        self.min_rows_for_od_model = min_rows_for_od_model
        self.models: Dict[Optional[Tuple[str, str]], TrainedModel] = {}  # {(origin,destination)|None: TrainedModel}

    # --- public API ---
    def train_all(self) -> Dict[str, Dict[str, float]]:
        """
        Train per-OD models and a global fallback model. Returns metrics summary.
        """
        df = self._load_dataframe()
        if df.empty:
            return {"global": {"error": "no data"}}

        # derive hour & day if not present
        if "hour" not in df.columns:
            df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
        if "day_of_week" not in df.columns:
            # Monday=0 … Sunday=6
            df["day_of_week"] = pd.to_datetime(df["timestamp"]).dt.dayofweek

        # Clean/filter
        df = df.dropna(subset=[TARGET_COLUMN] + REQUIRED_COLS).copy()
        df = df[(df[TARGET_COLUMN] > 0) & (df["distance_km"] >= 0)]

        metrics_report: Dict[str, Dict[str, float]] = {}

        # Train per-OD models where data is sufficient
        for (o, d), group in df.groupby(["origin", "destination"]):
            if len(group) < self.min_rows_for_od_model:
                continue
            model_key = (o, d)
            trained = self._train_one(group, model_key)
            self.models[model_key] = trained
            metrics_report[f"{o}->{d}"] = trained.metrics

        # Train global model as fallback
        global_trained = self._train_one(df, None)
        self.models[None] = global_trained
        metrics_report["global"] = global_trained.metrics

        return metrics_report

    def predict(
        self,
        origin: str,
        destination: str,
        hour: int,
        day_of_week: int,
        weather: str,
        traffic_level: str,
        distance_km: float,
        avg_speed_kmph: float,
    ) -> float:
        """
        Predict travel time (minutes) for a given OD + conditions.
        """
        x_row = pd.DataFrame([{
            "origin": origin,
            "destination": destination,
            "hour": int(hour),
            "day_of_week": int(day_of_week),
            "weather": str(weather),
            "traffic_level": str(traffic_level),
            "distance_km": float(distance_km),
            "avg_speed_kmph": float(avg_speed_kmph),
        }])

        # Prefer OD-specific model; fall back to global
        model = self.models.get((origin, destination)) or self.models.get(None)
        if model is None:
            raise RuntimeError("Models are not trained. Call train_all() first.")

        # The model pipeline expects only feature columns
        x = x_row[NUMERIC_COLS + CATEGORICAL_COLS]
        y_pred = model.pipeline.predict(x)[0]
        # Clamp to a reasonable range (avoid negative/huge outliers)
        return float(max(1.0, min(6 * 60, y_pred)))

    # --- internals ---
    def _train_one(self, df: pd.DataFrame, od_key: Optional[Tuple[str, str]]) -> TrainedModel:
        X = df[NUMERIC_COLS + CATEGORICAL_COLS]
        y = df[TARGET_COLUMN].values

        # Simple split (time-aware split could be used if needed)
        # Keep last 20% as validation
        split_idx = int(len(df) * 0.8)
        X_train, y_train = X.iloc[:split_idx], y[:split_idx]
        X_valid, y_valid = X.iloc[split_idx:], y[split_idx:]

        ct = ColumnTransformer(
            transformers=[
                ("ohe", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_COLS)
            ],
            remainder="passthrough",
        )

        model = Pipeline([
            ("prep", ct),
            ("rf", RandomForestRegressor(
                n_estimators=200,
                random_state=42,
                n_jobs=-1,
                min_samples_leaf=2,
                max_depth=None
            ))
        ])

        model.fit(X_train, y_train)

        y_hat = model.predict(X_valid) if len(X_valid) else np.array([])
        metrics = {}
        if len(y_hat):
            metrics["r2"] = float(r2_score(y_valid, y_hat))
            metrics["mae"] = float(mean_absolute_error(y_valid, y_hat))
        metrics["n_rows"] = int(len(df))
        key_str = f"{od_key[0]}->{od_key[1]}" if od_key else "global"
        metrics["model"] = key_str

        return TrainedModel(od_key=od_key, pipeline=model, metrics=metrics)

    def _load_dataframe(self) -> pd.DataFrame:
        """
        Loads all historical rows from SQLite. Expected table schema should contain at least:
          - origin, destination, timestamp, distance_km, avg_speed_kmph,
            weather, traffic_level, travel_time_min
        """
        with sqlite3.connect(self.db_path) as con:
            # Choose the table that holds your trip-level rows
            # Adjust table/column names if yours differ.
            # Example table name: trips
            # You can create a DB view if your data is scattered.
            try:
                df = pd.read_sql_query("SELECT * FROM trips", con)
            except Exception:
                # Fallback: try a more generic name
                df = pd.read_sql_query("SELECT * FROM traffic_history", con)

        # Ensure required columns exist; create safe defaults if missing
        for col in REQUIRED_COLS:
            if col not in df.columns:
                if col in ["hour", "day_of_week"]:
                    continue
                df[col] = np.nan

        # Coerce dtypes
        for c in ["distance_km", "avg_speed_kmph", TARGET_COLUMN]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        return df
