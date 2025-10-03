from __future__ import annotations
"""Baseline demand forecasting pipeline.

Method: hour-of-week mean (simple, fast, transparent) for covers per location.
Steps:
1. Load recent orders within training window.
2. Aggregate covers by location_id + hour_of_week (0..167).
3. Compute mean covers.
4. Forecast future horizon by mapping future timestamps -> hour_of_week and pulling mean (fallback to global mean if sparse).

Future upgrades:
- Replace with seasonal naive or Prophet per location.
- Incorporate weather/events features.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from ia.core.config import settings

# Reuse minimal copied models (import path depends on runtime app structure)
try:  # pragma: no cover - import flexibility
    from backend.app.main import Order, SessionLocal, ModelMetric  # type: ignore
except Exception:  # pragma: no cover
    Order = None  # type: ignore
    SessionLocal = None  # type: ignore
    ModelMetric = None  # type: ignore

import json
import math
import os

@dataclass
class HourOfWeekModel:
    version: str
    generated_at: datetime
    horizon_hours: int
    hour_means: Dict[int, float]  # hour_of_week -> mean covers
    global_mean: float

    def predict(self, timestamps: List[datetime]) -> List[float]:
        preds = []
        for ts in timestamps:
            how = (ts.weekday() * 24) + ts.hour
            preds.append(self.hour_means.get(how, self.global_mean))
        return preds

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "version": self.version,
                "generated_at": self.generated_at.isoformat(),
                "horizon_hours": self.horizon_hours,
                "hour_means": self.hour_means,
                "global_mean": self.global_mean,
            }, f)

    @staticmethod
    def load(path: str) -> "HourOfWeekModel":
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        return HourOfWeekModel(
            version=obj["version"],
            generated_at=datetime.fromisoformat(obj["generated_at"]),
            horizon_hours=int(obj["horizon_hours"]),
            hour_means={int(k): float(v) for k, v in obj["hour_means"].items()},
            global_mean=float(obj["global_mean"]),
        )


def _calc_hour_of_week(ts: datetime) -> int:
    return ts.weekday() * 24 + ts.hour


def train_hour_of_week_model(db: Session, window_days: int, horizon_hours: int) -> HourOfWeekModel:
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(days=window_days)

    rows = (
        db.query(Order.ts, Order.covers)
        .filter(Order.ts >= start, Order.ts < now)
        .all()
    )
    buckets: Dict[int, List[int]] = {}
    for ts, covers in rows:
        how = _calc_hour_of_week(ts)
        buckets.setdefault(how, []).append(int(covers))
    hour_means: Dict[int, float] = {}
    all_values: List[int] = []
    for how, vals in buckets.items():
        if not vals:
            continue
        hour_means[how] = sum(vals) / len(vals)
        all_values.extend(vals)
    global_mean = (sum(all_values) / len(all_values)) if all_values else 0.0

    model = HourOfWeekModel(
        version=f"how_mean_{now.strftime('%Y%m%d%H')}",
        generated_at=now,
        horizon_hours=horizon_hours,
        hour_means=hour_means,
        global_mean=global_mean,
    )
    return model


def persist_model(model: HourOfWeekModel) -> str:
    path = os.path.join(settings.MODEL_DIR, f"demand_{model.version}.json")
    model.save(path)
    # Optionally write/overwrite a symlink/latest pointer
    latest_ptr = os.path.join(settings.MODEL_DIR, "demand_latest.json")
    try:
        if os.path.islink(latest_ptr) or os.path.exists(latest_ptr):
            os.remove(latest_ptr)
        os.symlink(os.path.basename(path), latest_ptr)
    except Exception:
        # Fallback: copy contents
        with open(latest_ptr, "w", encoding="utf-8") as f_out:
            with open(path, "r", encoding="utf-8") as f_in:
                f_out.write(f_in.read())
    return path


def load_latest_model() -> HourOfWeekModel | None:
    path = os.path.join(settings.MODEL_DIR, "demand_latest.json")
    if not os.path.exists(path):
        return None
    try:
        return HourOfWeekModel.load(path)
    except Exception:
        return None


def ensure_trained(window_days: int | None = None, horizon_hours: int | None = None) -> HourOfWeekModel | None:
    window_days = window_days or settings.FORECAST_TRAINING_WINDOW_DAYS
    horizon_hours = horizon_hours or settings.FORECAST_DEFAULT_HORIZON_HOURS
    model = load_latest_model()
    if model:
        age_hours = (datetime.utcnow() - model.generated_at).total_seconds() / 3600.0
        if age_hours < 6:  # retrain every 6h baseline
            return model
    # Train new
    if SessionLocal is None or Order is None:
        return model  # cannot train without models
    db = SessionLocal()
    try:
        new_model = train_hour_of_week_model(db, window_days, horizon_hours)
        persist_model(new_model)
        # Log simple metrics if ModelMetric available
        if ModelMetric is not None:
            try:
                # Data volume metric
                total_rows = db.query(func.count(Order.id)).scalar() or 0
                mm1 = ModelMetric(model_name="demand_hour_of_week", version=new_model.version, metric_name="training_rows", value=float(total_rows))
                db.add(mm1)
                mm2 = ModelMetric(model_name="demand_hour_of_week", version=new_model.version, metric_name="global_mean_covers", value=float(new_model.global_mean))
                db.add(mm2)
                db.commit()
            except Exception:
                db.rollback()
        return new_model
    finally:
        db.close()
