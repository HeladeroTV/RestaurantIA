from __future__ import annotations

"""Central configuration for RestaurantIA.

Uses environment variables when present; falls back to sensible defaults for local dev.
Add new configuration keys here instead of scattering constants.
"""

from pydantic import BaseSettings, Field
from pathlib import Path
import os

class Settings(BaseSettings):
    # Database / storage
    DATABASE_URL: str = Field("sqlite:///./restaurantia.db", description="Primary application database URL")

    # Forecasting
    FORECAST_TRAINING_WINDOW_DAYS: int = Field(28, ge=7, le=120)
    FORECAST_DEFAULT_HORIZON_HOURS: int = Field(24, ge=1, le=240)
    FORECAST_MAX_HORIZON_HOURS: int = Field(168, ge=24, le=24*14)
    FORECAST_METHOD: str = Field("hour_of_week_mean_v1", description="Identifier for current production baseline method")

    # Paths
    MODEL_DIR: Path = Field(Path("models"), description="Directory where serialized models are stored")

    # MLflow (optional – if not set, training will skip logging gracefully)
    MLFLOW_TRACKING_URI: str | None = Field(None, description="MLflow tracking URI")
    MLFLOW_EXPERIMENT: str = Field("restaurantia", description="Default MLflow experiment name")

    class Config:
        env_prefix = "RESTAURANTIA_"
        case_sensitive = False

settings = Settings()

# Ensure model directory exists locally
os.makedirs(settings.MODEL_DIR, exist_ok=True)
