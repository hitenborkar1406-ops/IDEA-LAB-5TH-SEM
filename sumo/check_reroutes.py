import json
d = json.load(open('sim_output.json'))
events = d['reroute_events']
real = [e for e in events if e['old_edge'] != e['new_edge']]
print('total logged:', len(events))
print('genuine (edge actually changed):', len(real))
for e in real[:5]:
    print(e)