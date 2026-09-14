"""
Map & Congestion Engine.

Parses traffic_map_data.csv (267,836 predicted road-segment records)
and serves filtered edge segment metrics, geometries, and corridor hotspots.
"""

import os
import pandas as pd
from typing import Dict, List, Any, Optional

candidate_paths = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sumo", "traffic_map_data.csv")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sumo", "traffic_map_data.csv")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "sumo", "traffic_map_data.csv")),
    os.path.abspath(os.path.join(os.getcwd(), "sumo", "traffic_map_data.csv")),
]

DATA_PATH = next((p for p in candidate_paths if os.path.exists(p)), candidate_paths[0])


_df_cache: Optional[pd.DataFrame] = None
_grouped_cache: Dict[str, Dict[float, List[Dict[str, Any]]]] = {}

# Key Nagpur Landmarks & Congestion Hotspots
HOTSPOT_LANDMARKS = [
    {
        "id": "wardha_rd",
        "name": "Wardha Road Trunk Corridor",
        "keywords": ["wardha", "sitabuldi"],
        "lat": 21.125, "lng": 79.075, "x": 6386.12, "y": 5948.94
    },
    {
        "id": "ajni_sq",
        "name": "Ajni Square Junction",
        "keywords": ["ajni"],
        "lat": 21.118, "lng": 79.078, "x": 6476.39, "y": 5870.94
    },
    {
        "id": "kriplani_sq",
        "name": "Kriplani Square",
        "keywords": ["kriplani"],
        "lat": 21.122, "lng": 79.080, "x": 6585.00, "y": 5850.59
    },
    {
        "id": "rahate_colony",
        "name": "Rahate Colony Square",
        "keywords": ["rahate"],
        "lat": 21.130, "lng": 79.076, "x": 5050.18, "y": 5116.64
    },
    {
        "id": "lokmat_sq",
        "name": "Lokmat Square Cluster",
        "keywords": ["lokmat"],
        "lat": 21.135, "lng": 79.082, "x": 4994.45, "y": 5111.42
    }
]


def load_dataset() -> pd.DataFrame:
    global _df_cache
    if _df_cache is not None:
        return _df_cache

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"traffic_map_data.csv not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    _df_cache = df
    return df


def get_available_periods() -> Dict[str, Any]:
    df = load_dataset()
    periods = sorted(df["time_period"].unique().tolist())
    intervals = sorted(df["interval_begin_sec"].unique().tolist())

    # Map intervals to formatted clock strings
    def format_time(period: str, sec: float) -> str:
        base_hour = 9 if period.lower() == "morning" else 16
        total_minutes = int(sec // 60)
        hours = base_hour + (total_minutes // 60)
        mins = total_minutes % 60
        ampm = "AM" if hours < 12 else "PM"
        disp_hour = hours if hours <= 12 else hours - 12
        return f"{disp_hour:02d}:{mins:02d} {ampm} (+{total_minutes}m)"

    timeline = {}
    for p in periods:
        timeline[p] = [
            {
                "interval_sec": sec,
                "label": format_time(p, sec),
                "minute": int(sec // 60)
            }
            for sec in intervals
        ]

    return {
        "periods": periods,
        "intervals": intervals,
        "timeline": timeline
    }


def get_map_segments(time_period: str = "Morning", interval_sec: float = 0.0, limit: int = 5000) -> Dict[str, Any]:
    global _grouped_cache
    df = load_dataset()

    period_normalized = time_period.capitalize()
    if period_normalized not in df["time_period"].unique():
        period_normalized = "Morning"

    # Filter dataframe
    filtered = df[(df["time_period"] == period_normalized) & (df["interval_begin_sec"] == interval_sec)]
    if filtered.empty:
        # Fallback to closest available interval
        available_intervals = df[df["time_period"] == period_normalized]["interval_begin_sec"].unique()
        if len(available_intervals) > 0:
            interval_sec = available_intervals[0]
            filtered = df[(df["time_period"] == period_normalized) & (df["interval_begin_sec"] == interval_sec)]

    if limit and len(filtered) > limit:
        filtered = filtered.head(limit)

    segments = []
    class_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}

    for _, row in filtered.iterrows():
        cls = str(row.get("predicted_congestion_class", "LOW")).upper()
        if cls in class_counts:
            class_counts[cls] += 1

        segments.append({
            "edge_id": row["edge_id"],
            "flow": float(row.get("flow", 0.0)),
            "speed": round(float(row.get("speed", 0.0)), 1),
            "density": round(float(row.get("density", 0.0)), 1),
            "waitingTime": round(float(row.get("waitingTime", 0.0)), 1),
            "timeLoss": round(float(row.get("timeLoss", 0.0)), 1),
            "congestion_class": cls,
            "from_x": float(row.get("from_x", 0.0)),
            "from_y": float(row.get("from_y", 0.0)),
            "to_x": float(row.get("to_x", 0.0)),
            "to_y": float(row.get("to_y", 0.0)),
            "shape": str(row.get("shape", ""))
        })

    # Aggregated metrics
    avg_speed = round(filtered["speed"].mean(), 1) if not filtered.empty else 0.0
    avg_delay = round(filtered["timeLoss"].mean(), 1) if not filtered.empty else 0.0
    total_flow = int(filtered["flow"].sum()) if not filtered.empty else 0

    return {
        "time_period": period_normalized,
        "interval_sec": interval_sec,
        "total_segments": len(segments),
        "class_counts": class_counts,
        "summary": {
            "avgSpeedKmh": avg_speed,
            "avgDelaySec": avg_delay,
            "totalFlowVeh": total_flow
        },
        "hotspots": HOTSPOT_LANDMARKS,
        "segments": segments
    }


def get_hotspot_summary(time_period: str = "Morning", interval_sec: float = 0.0) -> List[Dict[str, Any]]:
    df = load_dataset()
    period_normalized = time_period.capitalize()
    filtered = df[(df["time_period"] == period_normalized) & (df["interval_begin_sec"] == interval_sec)]

    results = []
    for lm in HOTSPOT_LANDMARKS:
        # Match edges with keyword
        kw = lm["keywords"][0]
        mask = filtered["edge_id"].str.contains(kw, case=False, na=False)
        subset = filtered[mask]
        if subset.empty:
            subset = filtered  # Fallback

        avg_speed = round(subset["speed"].mean(), 1)
        avg_wait = round(subset["waitingTime"].mean(), 1)
        top_cls = subset["predicted_congestion_class"].mode()[0] if not subset.empty else "MODERATE"

        results.append({
            "id": lm["id"],
            "name": lm["name"],
            "avgSpeedKmh": avg_speed,
            "avgWaitSec": avg_wait,
            "congestionClass": top_cls,
            "location": {"x": lm["x"], "y": lm["y"]}
        })
    return results
