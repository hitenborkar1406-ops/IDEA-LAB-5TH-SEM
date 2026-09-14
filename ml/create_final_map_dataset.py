import pandas as pd

print("=" * 70)
print("CREATING FINAL MAP-READY TRAFFIC DATASET")
print("=" * 70)

# ------------------------------------------------------------
# FILES
# ------------------------------------------------------------

MORNING_PRED = "v2_morning_predictions.csv"
EVENING_PRED = "v2_evening_predictions.csv"

MORNING_GEOM = "morning_edge_geometry.csv"
EVENING_GEOM = "evening_edge_geometry.csv"

OUTPUT = "traffic_map_data.csv"

# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------

print("\nLoading Morning predictions...")
morning = pd.read_csv(MORNING_PRED)

print("Loading Evening predictions...")
evening = pd.read_csv(EVENING_PRED)

print("Loading Morning geometry...")
morning_geom = pd.read_csv(MORNING_GEOM)

print("Loading Evening geometry...")
evening_geom = pd.read_csv(EVENING_GEOM)

# ------------------------------------------------------------
# NORMALIZE COLUMNS
# ------------------------------------------------------------

# Morning prediction contains extra time columns.
# They are not needed for the final map dataset.

morning = morning.drop(
    columns=["interval_begin_time", "interval_end_time"],
    errors="ignore"
)

morning["time_period"] = "Morning"
evening["time_period"] = "Evening"

# ------------------------------------------------------------
# BASIC VALIDATION
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("INPUT VALIDATION")
print("=" * 70)

print("Morning prediction rows:", len(morning))
print("Evening prediction rows:", len(evening))

print("Morning prediction edges:", morning["edge_id"].nunique())
print("Evening prediction edges:", evening["edge_id"].nunique())

print("Morning geometry edges:", morning_geom["edge_id"].nunique())
print("Evening geometry edges:", evening_geom["edge_id"].nunique())

# ------------------------------------------------------------
# CHECK PREDICTION → GEOMETRY COVERAGE
# ------------------------------------------------------------

morning_missing = set(morning["edge_id"]) - set(morning_geom["edge_id"])
evening_missing = set(evening["edge_id"]) - set(evening_geom["edge_id"])

print("\nMorning prediction edges without geometry:", len(morning_missing))
print("Evening prediction edges without geometry:", len(evening_missing))

# ------------------------------------------------------------
# JOIN MORNING
# ------------------------------------------------------------

morning_map = morning.merge(
    morning_geom,
    on="edge_id",
    how="left",
    validate="many_to_one"
)

# ------------------------------------------------------------
# JOIN EVENING
# ------------------------------------------------------------

evening_map = evening.merge(
    evening_geom,
    on="edge_id",
    how="left",
    validate="many_to_one"
)

# ------------------------------------------------------------
# COMBINE
# ------------------------------------------------------------

combined = pd.concat(
    [morning_map, evening_map],
    ignore_index=True
)

# ------------------------------------------------------------
# GEOMETRY VALIDATION
# ------------------------------------------------------------

geometry_columns = [
    "from_x",
    "from_y",
    "to_x",
    "to_y",
    "shape"
]

missing_geometry = combined[geometry_columns].isna().sum()

print("\n" + "=" * 70)
print("FINAL GEOMETRY CHECK")
print("=" * 70)

print(missing_geometry)

# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

combined.to_csv(
    OUTPUT,
    index=False
)

# ------------------------------------------------------------
# FINAL REPORT
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FINAL MAP DATASET")
print("=" * 70)

print("Morning rows:", len(morning_map))
print("Evening rows:", len(evening_map))
print("Combined rows:", len(combined))

print("\nRows by period:")
print(combined["time_period"].value_counts())

print("\nUnique edges by period:")
print(
    combined.groupby("time_period")["edge_id"]
    .nunique()
)

print("\nPredicted classes:")
print(
    combined["predicted_congestion_class"]
    .value_counts()
)

print("\nClasses by period:")
print(
    combined.groupby(
        ["time_period", "predicted_congestion_class"]
    ).size()
)

print("\nGeometry missing:")
print(missing_geometry.to_dict())

print("\nOutput:", OUTPUT)

# ------------------------------------------------------------
# PASS / FAIL
# ------------------------------------------------------------

if (
    len(morning_missing) == 0
    and len(evening_missing) == 0
    and missing_geometry.sum() == 0
):
    print("\n" + "=" * 70)
    print("FINAL MAP DATASET: PASS")
    print("=" * 70)
else:
    print("\n" + "=" * 70)
    print("FINAL MAP DATASET: FAIL")
    print("=" * 70)