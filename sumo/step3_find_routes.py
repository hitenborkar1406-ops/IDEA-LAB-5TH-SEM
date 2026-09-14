"""
Step 3: Find OD pairs with multiple paths through the Sitabuldi junction
"""
import sys
sys.path.append(r'C:\Program Files (x86)\Eclipse\Sumo\tools')
import sumolib
from collections import defaultdict, deque

NET_FILE = "sitabuldi_junction.net.xml"
JUNCTION_ID = "cluster_2347019624_312691688_312691691"

print("Loading cropped network...")
net = sumolib.net.readNet(NET_FILE, withInternal=False)

target = net.getNode(JUNCTION_ID)
print(f"\nTarget junction: {JUNCTION_ID}")
print(f"Incoming edges: {[e.getID() for e in target.getIncoming()]}")
print(f"Outgoing edges: {[e.getID() for e in target.getOutgoing()]}")

# BFS to find paths between two nodes
def find_paths_bfs(net, start_edge_id, end_edge_id, max_depth=8):
    """Find up to 5 paths from start_edge to end_edge."""
    start_edge = net.getEdge(start_edge_id)
    end_edge = net.getEdge(end_edge_id)
    if not start_edge or not end_edge:
        return []
    
    start_node = start_edge.getToNode()
    end_node = end_edge.getFromNode()
    
    paths = []
    queue = deque([(start_node, [start_edge_id], 0)])
    visited_states = set()
    
    while queue and len(paths) < 5:
        node, path, depth = queue.popleft()
        
        if depth > max_depth:
            continue
        
        state = (node.getID(), tuple(path[-3:]))
        if state in visited_states:
            continue
        visited_states.add(state)
        
        if node.getID() == end_node.getID():
            paths.append(path + [end_edge_id])
            continue
        
        for edge in node.getOutgoing():
            if edge.getID() not in path:  # avoid cycles
                queue.append((edge.getToNode(), path + [edge.getID()], depth + 1))
    
    return paths

# Look at the outgoing edges from the target junction - these are the "approach roads"
# Find incoming edges to the junction as potential origins
incoming = list(target.getIncoming())
outgoing = list(target.getOutgoing())

print(f"\n=== Approach roads to Sitabuldi junction ===")
print(f"\nIncoming (potential origins, one hop back):")
for edge in incoming:
    from_node = edge.getFromNode()
    # Look further back
    prev_edges = from_node.getIncoming()
    print(f"  -> {edge.getID()} (len={edge.getLength():.0f}m, speed={edge.getSpeed():.1f}m/s) from {from_node.getID()}")
    for pe in prev_edges[:3]:
        print(f"       <- {pe.getID()} (len={pe.getLength():.0f}m)")

print(f"\nOutgoing (potential destinations, one hop forward):")
for edge in outgoing:
    to_node = edge.getToNode()
    next_edges = to_node.getOutgoing()
    print(f"  -> {edge.getID()} (len={edge.getLength():.0f}m, speed={edge.getSpeed():.1f}m/s) to {to_node.getID()}")
    for ne in next_edges[:3]:
        print(f"       -> {ne.getID()} (len={ne.getLength():.0f}m)")

# Try to find OD pairs with multiple paths
# Look for edges with decent length (>100m) that connect via the junction
print(f"\n=== Searching for multi-path OD pairs through the junction ===")

# Specifically try longer edges near the junction
# Let's find edges from 2 hops before to 2 hops after the junction
two_hop_in = set()
two_hop_out = set()

for in_edge in target.getIncoming():
    two_hop_in.add(in_edge.getID())
    for prev_edge in in_edge.getFromNode().getIncoming():
        two_hop_in.add(prev_edge.getID())

for out_edge in target.getOutgoing():
    two_hop_out.add(out_edge.getID())
    for next_edge in out_edge.getToNode().getOutgoing():
        two_hop_out.add(next_edge.getID())

print(f"\n2-hop in edges: {two_hop_in}")
print(f"\n2-hop out edges: {two_hop_out}")

# Let's find a pair that allows two paths
# The key is to pick an origin that feeds into the junction AND a destination beyond it
# but also has an alternate route that bypasses the junction

# Try: large parallel roads around the junction
# Origin: one of the long approach roads BEFORE the junction
# Destination: one of the long roads AFTER the junction
# But also find if there's a bypass

# Filter longer edges
all_edges = [e for e in net.getEdges() if e.getLength() > 100]
print(f"\nEdges > 100m: {len(all_edges)}")

# Get connected components via DFS to check full connectivity
def get_reachable_edges(net, from_edge_id, max_hops=6):
    """Find all edges reachable from from_edge within max_hops."""
    reachable = {}
    queue = deque([(from_edge_id, 0)])
    while queue:
        edge_id, hops = queue.popleft()
        if edge_id in reachable or hops > max_hops:
            continue
        reachable[edge_id] = hops
        edge = net.getEdge(edge_id)
        if edge:
            for next_edge in edge.getToNode().getOutgoing():
                if next_edge.getID() not in reachable:
                    queue.append((next_edge.getID(), hops + 1))
    return reachable

# Pick a specific origin: look for a major incoming road to the junction
# Use -200033871 or similar as origin (approaches to Sitabuldi)
# Let's check what the most promising longer edges near the junction are

# Find reachable set from each 2-hop-in edge
best_od_pairs = []
print("\n--- Testing origin/destination pairs ---")
for orig_id in list(two_hop_in)[:8]:
    orig = net.getEdge(orig_id)
    if not orig or orig.getLength() < 50:
        continue
    reachable = get_reachable_edges(net, orig_id, max_hops=5)
    # Check if any good destination is reachable
    for dest_id in list(two_hop_out)[:8]:
        if dest_id in reachable and dest_id != orig_id:
            dest = net.getEdge(dest_id)
            if dest and dest.getLength() > 50:
                paths = find_paths_bfs(net, orig_id, dest_id, max_depth=6)
                if len(paths) >= 2:
                    print(f"\n  FOUND: {orig_id} -> {dest_id}: {len(paths)} paths")
                    for i, p in enumerate(paths):
                        path_len = sum(net.getEdge(e).getLength() for e in p if net.getEdge(e))
                        print(f"    Path {i+1} ({path_len:.0f}m total): {' -> '.join(p)}")
                    best_od_pairs.append((orig_id, dest_id, paths))

if not best_od_pairs:
    print("\nNo multi-path pairs found in 2-hop set. Trying broader search...")
    # Try with incoming -> deeper destination edges
    for orig_id in list(two_hop_in):
        orig = net.getEdge(orig_id)
        if not orig or orig.getLength() < 100:
            continue
        reachable = get_reachable_edges(net, orig_id, max_hops=8)
        for dest_id in list(reachable.keys()):
            if dest_id == orig_id:
                continue
            dest = net.getEdge(dest_id)
            if not dest or dest.getLength() < 100:
                continue
            paths = find_paths_bfs(net, orig_id, dest_id, max_depth=8)
            if len(paths) >= 2:
                diffs = set(frozenset(p) for p in paths)
                if len(diffs) >= 2:  # genuinely different paths
                    print(f"\n  FOUND: {orig_id} -> {dest_id}: {len(paths)} distinct paths")
                    for i, p in enumerate(paths[:2]):
                        path_len = sum(net.getEdge(e).getLength() for e in p if net.getEdge(e))
                        print(f"    Path {i+1} ({path_len:.0f}m): {' -> '.join(p)}")
                    best_od_pairs.append((orig_id, dest_id, paths))
                    if len(best_od_pairs) >= 3:
                        break
        if len(best_od_pairs) >= 3:
            break

if best_od_pairs:
    orig_id, dest_id, paths = best_od_pairs[0]
    print(f"\n=== SELECTED OD PAIR ===")
    print(f"  Origin      : {orig_id}")
    print(f"  Destination : {dest_id}")
    print(f"  Path count  : {len(paths)}")
    for i, p in enumerate(paths[:2]):
        path_len = sum(net.getEdge(e).getLength() for e in p if net.getEdge(e))
        print(f"  Path {i+1} ({path_len:.0f}m): {p}")
else:
    print("\nNo multi-path pairs found! Need wider crop or different approach.")
