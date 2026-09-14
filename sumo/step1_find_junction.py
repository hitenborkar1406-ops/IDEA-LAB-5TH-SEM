"""
Step 1: Find the best junction near Sitabuldi Square, Nagpur (~21.146, 79.085)
Uses UTM Zone 44N projection with netOffset to convert XY -> lon/lat without pyproj.
Network projection: +proj=utm +zone=44 +ellps=WGS84 +datum=WGS84 +units=m +no_defs
NetOffset: -292445.79, -2333350.41
"""
import sys
sys.path.append(r'C:\Program Files (x86)\Eclipse\Sumo\tools')
import sumolib
import math

NET_FILE = "osm.net.xml"
SITABULDI_LAT = 21.146
SITABULDI_LON = 79.085

# Network parameters from the <location> tag
NET_OFFSET_X = -292445.79
NET_OFFSET_Y = -2333350.41
# UTM Zone 44N conversion constants
UTM_ZONE = 44
K0 = 0.9996
E = 0.00669438
E2 = E * E
E3 = E2 * E
E_P2 = E / (1.0 - E)
SQRT_E = math.sqrt(1 - E)
_E = (1 - SQRT_E) / (1 + SQRT_E)
_E2 = _E * _E
_E3 = _E2 * _E
_E4 = _E3 * _E
_E5 = _E4 * _E
M1 = (1 - E / 4 - 3 * E2 / 64 - 5 * E3 / 256)
M2 = (3 * E / 8 + 3 * E2 / 32 + 45 * E3 / 1024)
M3 = (15 * E2 / 256 + 45 * E3 / 1024)
M4 = (35 * E3 / 3072)
P2 = (3. / 2 * _E - 27. / 32 * _E3 + 269. / 512 * _E5)
P3 = (21. / 16 * _E2 - 55. / 32 * _E4)
P4 = (151. / 96 * _E3 - 417. / 128 * _E5)
P5 = (1097. / 512 * _E4)
R = 6378137

def utm44n_to_lonlat(easting, northing):
    """Convert UTM Zone 44N easting/northing to lon/lat (WGS84)."""
    zone_number = UTM_ZONE
    zone_letter = 'N'  # Northern hemisphere
    x = easting - 500000
    y = northing
    m = y / K0
    mu = m / (R * M1)
    p_rad = (mu + P2 * math.sin(2 * mu) + P3 * math.sin(4 * mu) +
             P4 * math.sin(6 * mu) + P5 * math.sin(8 * mu))
    p_sin = math.sin(p_rad)
    p_sin2 = p_sin * p_sin
    p_cos = math.cos(p_rad)
    p_tan = p_sin / p_cos
    p_tan2 = p_tan * p_tan
    p_tan4 = p_tan2 * p_tan2
    ep_sin = 1 - E * p_sin2
    ep_sin_sqrt = math.sqrt(1 - E * p_sin2)
    n = R / ep_sin_sqrt
    r = (1 - E) / ep_sin
    c = E_P2 * p_cos ** 2
    c2 = c * c
    d = x / (n * K0)
    d2 = d * d
    d3 = d2 * d
    d4 = d3 * d
    d5 = d4 * d
    d6 = d5 * d
    latitude = (p_rad - (p_tan / r) *
                (d2 / 2 - d4 / 24 * (5 + 3 * p_tan2 + 10 * c - 4 * c2 - 9 * E_P2)) +
                d6 / 720 * (61 + 90 * p_tan2 + 298 * c + 45 * p_tan4 - 252 * E_P2 - 3 * c2))
    longitude = (d - d3 / 6 * (1 + 2 * p_tan2 + c) +
                 d5 / 120 * (5 - 2 * c + 28 * p_tan2 - 3 * c2 + 8 * E_P2 + 24 * p_tan4)) / p_cos
    longitude = math.degrees(longitude) + (zone_number - 1) * 6 - 180 + 3
    latitude = math.degrees(latitude)
    return longitude, latitude

def sumo_xy_to_lonlat(x, y):
    """Convert SUMO net XY to lon/lat using net offset and UTM Zone 44N."""
    # Reverse the netOffset: sumo_xy = utm_coord + netOffset => utm = sumo_xy - netOffset
    utm_e = x - NET_OFFSET_X
    utm_n = y - NET_OFFSET_Y
    return utm44n_to_lonlat(utm_e, utm_n)

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

print("Loading network...")
net = sumolib.net.readNet(NET_FILE, withInternal=False)
print(f"Network loaded. Junctions: {len(net.getNodes())}, Edges: {len(net.getEdges())}")

# Verify the conversion with a known boundary point
# origBoundary="79.001743,21.090212,79.148815,21.162234"
# convBoundary="0.00,-0.00,15330.92,7971.84"
test_lon, test_lat = sumo_xy_to_lonlat(0.0, 0.0)
print(f"\nVerification (XY 0,0 should be ~79.0017, 21.0902): lon={test_lon:.4f}, lat={test_lat:.4f}")
test_lon2, test_lat2 = sumo_xy_to_lonlat(15330.92, 7971.84)
print(f"Verification (XY max should be ~79.1488, 21.1622): lon={test_lon2:.4f}, lat={test_lat2:.4f}")

# Count connectivity for each junction
junction_conn = []
for node in net.getNodes():
    incoming = len(node.getIncoming())
    outgoing = len(node.getOutgoing())
    total = incoming + outgoing
    junction_conn.append((total, incoming, outgoing, node))

junction_conn.sort(key=lambda x: -x[0])

print("\n=== Top 20 junctions by connectivity ===")
print(f"{'Rank':<5} {'Total':<7} {'In':<5} {'Out':<5} {'Junction ID':<50} {'Lon':<12} {'Lat':<12} {'Dist_km':<10}")
print("-" * 115)

all_with_dist = []
for rank, (total, inc, out, node) in enumerate(junction_conn[:20], 1):
    x, y = node.getCoord()
    lon, lat = sumo_xy_to_lonlat(x, y)
    dist_km = haversine_km(SITABULDI_LAT, SITABULDI_LON, lat, lon)
    all_with_dist.append((dist_km, total, inc, out, node, lon, lat, x, y))
    print(f"{rank:<5} {total:<7} {inc:<5} {out:<5} {node.getID():<50} {lon:<12.6f} {lat:<12.6f} {dist_km:<10.4f}")

print("\n=== Top 20 sorted by distance to Sitabuldi Square (~21.146, 79.085) ===")
all_with_dist.sort(key=lambda x: x[0])
print(f"\n{'Rank':<5} {'Dist_km':<10} {'Total':<7} {'ID':<50} {'Lon':<12} {'Lat':<12}")
print("-" * 100)
for rank, (dist_km, total, inc, out, node, lon, lat, x, y) in enumerate(all_with_dist, 1):
    print(f"{rank:<5} {dist_km:<10.4f} {total:<7} {node.getID():<50} {lon:<12.6f} {lat:<12.6f}")

best = all_with_dist[0]
dist_km, total, inc, out, node, lon, lat, x, y = best
print(f"\n=== CHOSEN JUNCTION ===")
print(f"  ID          : {node.getID()}")
print(f"  Connectivity: {total} ({inc} in + {out} out)")
print(f"  Lon/Lat     : {lon:.6f}, {lat:.6f}")
print(f"  Distance    : {dist_km:.4f} km from Sitabuldi ({dist_km*1000:.1f} m)")
print(f"  XY (net)    : ({x:.2f}, {y:.2f})")
print(f"  Type        : {node.getType()}")

# Also store for later use
print(f"\n  JUNCTION_ID = \"{node.getID()}\"")
print(f"  JUNCTION_X  = {x:.2f}")
print(f"  JUNCTION_Y  = {y:.2f}")
