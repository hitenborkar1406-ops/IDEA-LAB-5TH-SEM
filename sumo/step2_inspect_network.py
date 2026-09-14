"""
Step 2 validation + Step 3 prep: Inspect the cropped network
"""
import sys
sys.path.append(r'C:\Program Files (x86)\Eclipse\Sumo\tools')
import sumolib

NET_FILE = "sitabuldi_junction.net.xml"

print("Loading cropped network...")
net = sumolib.net.readNet(NET_FILE, withInternal=False)
nodes = net.getNodes()
edges = net.getEdges()
print(f"\nCropped network stats:")
print(f"  Junctions: {len(nodes)}")
print(f"  Edges    : {len(edges)}")

# Check if the chosen junction exists
JUNCTION_ID = "cluster_2347019624_312691688_312691691"
target = net.getNode(JUNCTION_ID)
if target:
    print(f"\n  Target junction '{JUNCTION_ID}' FOUND in cropped network!")
    print(f"  Incoming edges: {[e.getID() for e in target.getIncoming()]}")
    print(f"  Outgoing edges: {[e.getID() for e in target.getOutgoing()]}")
else:
    print(f"\n  WARNING: Target junction '{JUNCTION_ID}' NOT found in cropped network!")

print("\n=== All edges in cropped network ===")
print(f"{'Edge ID':<40} {'From':<35} {'To':<35} {'Length_m':<10} {'Lanes':<6} {'Speed':<8}")
print("-" * 140)
for edge in sorted(edges, key=lambda e: e.getID()):
    fr = edge.getFromNode().getID()
    to = edge.getToNode().getID()
    length = edge.getLength()
    lanes = edge.getLaneNumber()
    speed = edge.getSpeed()
    print(f"{edge.getID():<40} {fr:<35} {to:<35} {length:<10.1f} {lanes:<6} {speed:<8.1f}")

print(f"\n=== Finding viable OD pairs for routes ===")
print("Looking for pairs with length > 200m and at least 2 paths...")

# Find edges that are long enough to be useful origins/destinations
long_edges = [(e.getLength(), e) for e in edges if e.getLength() > 50]
long_edges.sort(reverse=True)
print(f"\nTop 15 longest edges:")
print(f"{'Length_m':<10} {'Edge ID':<40} {'From':<35} {'To'}")
for length, edge in long_edges[:15]:
    print(f"{length:<10.1f} {edge.getID():<40} {edge.getFromNode().getID():<35} {edge.getToNode().getID()}")
