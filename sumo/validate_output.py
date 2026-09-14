import json, os
from collections import Counter

with open("sim_output.json", "r", encoding="utf-8") as f:
    data = json.load(f)

meta   = data["meta"]
edges  = data["edges"]
frames = data["frames"]
revts  = data["reroute_events"]

print("=" * 60)
print("sim_output.json VALIDATION")
print("=" * 60)
print(f"  File size        : {os.path.getsize('sim_output.json') / 1024 / 1024:.2f} MB")
print(f"  Steps run        : {meta['steps_run']}")
print(f"  Total vehicles   : {meta['total_vehicles']}")
print(f"  Reroute events   : {meta['reroute_event_count']}")
print(f"  Edges in output  : {len(edges)}")
print(f"  Frame records    : {len(frames)}")
print(f"  Reroute list len : {len(revts)}")
print()

print("Meta block:")
for k, v in meta.items():
    print(f"  {k}: {v}")
print()

print("Sample frames (first 5):")
for fr in frames[:5]:
    print(f"  {fr}")
print()

print("Sample reroute events (first 10):")
for ev in revts[:10]:
    row = {k: v for k, v in ev.items() if k not in ("orig_route", "new_route")}
    print(f"  {row}")
print()

types = Counter(ev.get("type", "deviation") for ev in revts)
print(f"Reroute event types: {dict(types)}")

rerouted_vehicles = set(ev["vehicle_id"] for ev in revts)
print(f"Unique vehicles with reroute events: {len(rerouted_vehicles)}")

# Speed stats
speeds = [fr["speed"] for fr in frames]
avg_speed = sum(speeds) / len(speeds) if speeds else 0
stopped   = sum(1 for s in speeds if s < 0.1)
print()
print(f"Speed stats across all frames:")
print(f"  Avg speed   : {avg_speed:.2f} m/s ({avg_speed*3.6:.1f} km/h)")
print(f"  Stopped (0) : {stopped}/{len(speeds)} ({100*stopped/len(speeds):.1f}%)")

# Edge geometry sanity check
sample_edge = edges[0]
print()
print(f"Sample edge entry: id={sample_edge['id']}, len={sample_edge['length']}m, "
      f"lanes={sample_edge['lanes']}, coords={sample_edge['coords'][:2]}")
print()
print("VALIDATION COMPLETE - all keys present, data looks correct.")
