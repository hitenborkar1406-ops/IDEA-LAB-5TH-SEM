import gzip
import xml.etree.ElementTree as ET
import pandas as pd

NET_FILE = "osm.net.xml.gz"
OUTPUT_FILE = "evening_edge_geometry.csv"

print("=" * 70)
print("REBUILDING SUMO EDGE GEOMETRY — V2")
print("=" * 70)

with gzip.open(NET_FILE, "rb") as f:
    root = ET.parse(f).getroot()

rows = []

for edge in root.findall("edge"):

    edge_id = edge.attrib.get("id")

    if not edge_id:
        continue

    # Exclude SUMO internal junction edges only
    if edge_id.startswith(":"):
        continue

    from_node = edge.attrib.get("from")
    to_node = edge.attrib.get("to")

    lanes = edge.findall("lane")

    if not lanes:
        continue

    # Use the first lane as representative geometry
    lane = lanes[0]

    shape = lane.attrib.get("shape")

    if not shape:
        continue

    # Parse first and last coordinates from lane shape
    points = []

    for point in shape.split():
        try:
            x, y = point.split(",")
            points.append(
                (float(x), float(y))
            )
        except ValueError:
            continue

    if len(points) < 2:
        continue

    from_x, from_y = points[0]
    to_x, to_y = points[-1]

    rows.append({
        "edge_id": edge_id,
        "from_node": from_node,
        "to_node": to_node,
        "from_x": from_x,
        "from_y": from_y,
        "to_x": to_x,
        "to_y": to_y,
        "shape": shape
    })


df = pd.DataFrame(rows)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 70)
print("GEOMETRY REBUILD COMPLETE")
print("=" * 70)

print("Edges extracted:", len(df))
print("Unique edge IDs:", df["edge_id"].nunique())

print("\nMissing values:")
print(df.isna().sum())

print("\nOutput:", OUTPUT_FILE)
print("=" * 70)
