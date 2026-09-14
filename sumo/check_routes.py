import sumolib
net = sumolib.net.readNet('sitabuldi_junction.net.xml')

def check(name, route_edges):
    ids = route_edges.split()
    total_len = 0
    print(f'{name}:')
    for i in range(len(ids)-1):
        e1 = net.getEdge(ids[i])
        e2 = net.getEdge(ids[i+1])
        connected = e1.getToNode() == e2.getFromNode()
        total_len += e1.getLength()
        print(f'  {ids[i]} -> {ids[i+1]} : connected={connected}')
    total_len += net.getEdge(ids[-1]).getLength()
    print(f'  total length: {total_len:.1f}m\n')

main = '-93465710#10 -225888744#0 27110922#14 -27110922#14'
side = '-93465710#10 -225888744#0 -27110922#12 27110922#12 27110922#14 -27110922#14'
check('MAIN ROAD', main)
check('SIDE STREET', side)