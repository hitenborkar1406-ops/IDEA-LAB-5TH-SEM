import json
d = json.load(open('sim_output.json'))
d['reroute_events'] = [e for e in d['reroute_events'] if e['old_edge'] != e['new_edge']]
# traffic_lights array is already keyed per (id, time) — pass through as-is
if 'traffic_lights' not in d:
    d['traffic_lights'] = []
json.dump(d, open('sim_output_clean.json', 'w'))
print('genuine reroutes kept:', len(d['reroute_events']))
print('traffic_light records:', len(d['traffic_lights']))