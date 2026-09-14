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

    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        _df_cache = df
        return df

    # Auto-generate if missing on cloud host
    try:
        sumo_dir = os.path.dirname(DATA_PATH)
        m_geom = os.path.join(sumo_dir, "morning_edge_geometry.csv")
        e_geom = os.path.join(sumo_dir, "evening_edge_geometry.csv")
        if os.path.exists(m_geom) and os.path.exists(e_geom):
            from sumo.generate_traffic_map_data import generate_period
            m_df = pd.read_csv(m_geom)
            e_df = pd.read_csv(e_geom)
            m_data = generate_period(m_df, "Morning")
            e_data = generate_period(e_df, "Evening")
            df = pd.concat([m_data, e_data], ignore_index=True)
            _df_cache = df
            return df
    except Exception as exc:
        print(f"Dataset generation failed: {exc}")

    # Fallback to empty DataFrame with expected columns
    df = pd.DataFrame(columns=[
        "edge_id", "interval_begin_sec", "time_period", "flow", "speed",
        "density", "waitingTime", "timeLoss", "predicted_congestion_class",
        "from_x", "from_y", "to_x", "to_y", "shape"
    ])
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
    df = load_dataset()

    period_normalized = time_period.capitalize()
    if period_normalized not in df["time_period"].unique():
        period_normalized = "Morning"

    # Match interval
    try:
        req_interval = float(interval_sec)
    except (ValueError, TypeError):
        req_interval = 0.0

    filtered = df[(df["time_period"] == period_normalized) & (df["interval_begin_sec"] == req_interval)]
    if filtered.empty:
        available_intervals = df[df["time_period"] == period_normalized]["interval_begin_sec"].unique()
        if len(available_intervals) > 0:
            req_interval = float(available_intervals[0])
            filtered = df[(df["time_period"] == period_normalized) & (df["interval_begin_sec"] == req_interval)]

    if limit and len(filtered) > limit:
        filtered = filtered.head(limit)

    segments = []
    class_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}

    for _, row in filtered.iterrows():
        cls = str(row.get("predicted_congestion_class", "LOW")).upper()
        if cls not in class_counts:
            cls = "LOW"
        class_counts[cls] += 1

        segments.append({
            "edge_id": str(row.get("edge_id", "")),
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

    # Aggregated metrics (NaN-safe)
    speed_mean = filtered["speed"].dropna().mean() if not filtered.empty else 28.5
    avg_speed = round(float(speed_mean), 1) if not np.isnan(speed_mean) else 28.5

    delay_mean = filtered["timeLoss"].dropna().mean() if not filtered.empty else 18.0
    avg_delay = round(float(delay_mean), 1) if not np.isnan(delay_mean) else 18.0

    flow_sum = filtered["flow"].dropna().sum() if not filtered.empty else 14500
    total_flow = int(flow_sum) if not np.isnan(flow_sum) else 14500

    return {
        "time_period": period_normalized,
        "interval_sec": req_interval,
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
    if period_normalized not in df["time_period"].unique():
        period_normalized = "Morning"

    try:
        req_interval = float(interval_sec)
    except (ValueError, TypeError):
        req_interval = 0.0

    filtered = df[(df["time_period"] == period_normalized) & (df["interval_begin_sec"] == req_interval)]
    if filtered.empty:
        available_intervals = df[df["time_period"] == period_normalized]["interval_begin_sec"].unique()
        if len(available_intervals) > 0:
            filtered = df[(df["time_period"] == period_normalized) & (df["interval_begin_sec"] == float(available_intervals[0]))]

    results = []
    for lm in HOTSPOT_LANDMARKS:
        subset = filtered
        if not filtered.empty and "from_x" in filtered.columns and "from_y" in filtered.columns:
            lx, ly = lm["x"], lm["y"]
            dx = filtered["from_x"] - lx
            dy = filtered["from_y"] - ly
            dist_sq = dx * dx + dy * dy
            sorted_indices = np.argsort(dist_sq.values)[:80]
            subset = filtered.iloc[sorted_indices]

        # Safe non-NaN calculations
        s_mean = subset["speed"].dropna().mean() if not subset.empty else 22.0
        avg_speed = round(float(s_mean), 1) if not np.isnan(s_mean) else 22.0

        w_mean = subset["waitingTime"].dropna().mean() if not subset.empty else 25.0
        avg_wait = round(float(w_mean), 1) if not np.isnan(w_mean) else 25.0

        if not subset.empty and not subset["predicted_congestion_class"].dropna().empty:
            modes = subset["predicted_congestion_class"].dropna().mode()
            top_cls = str(modes[0]) if len(modes) > 0 else "MODERATE"
        else:
            top_cls = "HIGH" if avg_speed < 18 else ("MEDIUM" if avg_speed < 30 else "LOW")

        results.append({
            "id": lm["id"],
            "name": lm["name"],
            "avgSpeedKmh": avg_speed,
            "avgWaitSec": avg_wait,
            "congestionClass": top_cls,
            "location": {"x": lm["x"], "y": lm["y"]}
        })
    return results
