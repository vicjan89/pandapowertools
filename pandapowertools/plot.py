import pandapower as pp
from textengines.interfaces import *
from pandapowertools.functions import split_str

dx = 2
r = 0.1
text_size = 0.2

def _node(x, y, text, te: TextEngine):
    if isinstance(text, str):
        text = [text]
    te.circle(x, y, r=r, black=False)
    dy = text_size * 1.2
    for t in text:
        if len(t) > 8:
            txts = split_str(t, 8)
            for txt in txts[::-1]:
                te.label(x, y, text=txt, s=text_size, place='ne')
                y += dy
        else:
            te.label(x, y, text=t, s=text_size, place='ne')
            y += dy


def _bus(x, y, quantity, text, te: TextEngine):
    if isinstance(text, str):
        text = [text]
    quantity -= 1
    d = dx / 2
    dr = r * 1.5
    te.lines((x-d, y-dr), (x-d, y+dr), (x+(quantity-1) * dx + d, y + dr), (x+(quantity-1) * dx + d, y - dr),
             cycle=True)
    for i in range(quantity):
        te.circle(x+i * dx, y, r=r, black=False)
    dy = text_size * 1.2
    for t in text:
        te.label(x-0.3, y+0.1, text=t, place='ne', s=text_size)
        y += dy

def _line_straight(*args, te: TextEngine, text: str = ''):
    if isinstance(text, str):
        text = [text]
    if len(args) == 2:
        (x1, y1), (x2, y2) = args
        te.lines((x1, y1), (x2, y2))
    for t in text:
        te.label(x=(x1+x2)/2, y=(y1+y2)/2, s=text_size, place='ne', angle=90, text=t)


def _line(*args, te: TextEngine, text: str = ''):
    if isinstance(text, str):
        text = [text]
    if len(args) == 2:
        (x1, y1), (x2, y2) = args
        if y2 > y1:
            x2 = x1
            y2 -= r
            y1 += r
        else:
            x1 = x2
            y2 += r
            y1 -= r
        te.lines((x1, y1), (x2, y2))
    else:
        te.lines(*args)
    y = min(y1, y2)
    for t in text:
        te.label(x=x1-r*2, y=y+r, s=text_size, place='ne', angle=90, text=t)

def _impedance(x1, y1, x2, y2, te: TextEngine):
    x2 = x1
    y2 += r
    y1 -= r
    y_midle = (y1 + y2) / 2
    r_impedance = r * 4
    te.circle(x1, y_midle, r=r_impedance, st_angle=180, en_angle=90, black=False)
    te.lines((x1, y1), (x2, y_midle+r_impedance))
    te.lines((x2, y2), (x1, y_midle), (x1-r_impedance, y_midle))

def _trafo(x1, y1, x2, y2, text, te: TextEngine):
    if y2 > y1:
        x1, y1, x2, y2 = x2, y2, x1, y1
    x1 = x2
    y2 += r
    y1 -= r
    y_midle = (y1 + y2) / 2
    r_trafo = r * 4
    te.circle(x1, y_midle+r_trafo-r, r=r_trafo, black=False)
    te.circle(x1, y_midle-r_trafo+r, r=r_trafo, black=False)
    te.lines((x1, y1), (x2, y_midle+r_trafo * 2 - r))
    te.lines((x2, y2), (x1, y_midle-r_trafo * 2 + r))
    if isinstance(text, str):
        text = [text]
    dy = text_size * 1.2
    for t in text:
        if len(t) > 6:
            txts = split_str(t, 6)
            for txt in txts[::-1]:
                te.label(x1 + r_trafo-r, y_midle, text=txt, place='e', s=text_size)
                y_midle += dy
        else:
            te.label(x1 + r_trafo - r, y_midle, text=t, place='e', s=text_size)
            y_midle += dy

def _trafo3w(x1, y1, x2, y2, x3, y3, text, te: TextEngine):
    y1 -= r
    y2 += r
    y3 += r
    y_midle = (y1 + max(y2, y3)) / 2
    r_trafo = r * 4
    r2 = r * 2
    te.circle(x1, y_midle+r_trafo-r, r=r_trafo, black=False)
    te.circle(x1-r2-r, y_midle-r_trafo+r, r=r_trafo, black=False)
    te.circle(x1+r2+r, y_midle-r_trafo+r, r=r_trafo, black=False)
    te.lines((x1, y1), (x1, y_midle+r_trafo * 2 - r))
    y = y_midle-r_trafo + r
    te.lines((x2, y2), (x2, y), (x1-r2-r-r_trafo, y))
    te.lines((x3, y3), (x3, y), (x1+r2+r+r_trafo, y))
    if isinstance(text, str):
        text = [text]
    dy = text_size * 1.2
    y_midle += r
    for t in text:
        te.label(x1 + r + r_trafo, y_midle, text=t, place='e', s=text_size)
        y_midle -= dy

def _ext_grid(x, y, te: TextEngine):
    d = 0.5
    d2 = d * 2
    d3 = d * 3
    d4 = d * 4
    dy = 0.5
    te.lines((x, y+r), (x, y+d2+dy))
    te.lines((x-d, y+d2+dy),(x-d, y+d4+dy), (x+d, y+d4+dy), (x+d, y+d2+dy), cycle=True)
    te.lines((x-d, y+d2+dy), (x+d, y+d4+dy))
    te.lines((x-d, y+d3+dy), (x, y+d4+dy))
    te.lines((x, y+d2+dy), (x+d, y+d3+dy))
    te.lines((x+d, y+d2+dy), (x-d, y+d4+dy))
    te.lines((x+d, y+d3+dy), (x, y+d4+dy))
    te.lines((x, y+d2+dy), (x-d, y+d3+dy))

def _gen(x, y, text, te: TextEngine):
    d = 0.5
    d2 = d * 2
    r_gen = r * 4
    y_midle = y - r_gen * 2
    te.lines((x, y-r), (x, y - r_gen))
    te.circle(x, y_midle, r_gen)
    if isinstance(text, str):
        text = [text]
    dy = text_size * 1.2
    te.label(x, y_midle, 'G', 'c', s=text_size)
    te.label(x, y_midle, '~', 's', s=text_size)
    for t in text:
        te.label(x + r + r_gen, y_midle, text=t, place='e', s=text_size)
        y_midle -= dy

def plot(net: pp.pandapowerNet, te: TextEngine, indexes: bool = True, ikz: bool = False, line_straight: bool = True,
         voltage: bool = True):
    '''
    Plot pandapowerNet to TextEngine format
    :param net:
    :param te:
    :param indexes: if True then plot inexes
    :return:
    '''
    #plot buses
    nodes = []
    buses = []
    bus_coords = {}
    for i, bus in net.bus.iterrows():
        connected = pp.toolbox.get_connected_elements_dict(net=net, buses=[i])
        quantity = sum([len(item) for key, item in connected.items() if key != 'bus'])
        if quantity > 3:
            buses.append((i, quantity))
        else:
            nodes.append(i)
        bus_coords[i] = (net.bus_geodata.loc[i, 'x'], net.bus_geodata.loc[i, 'y'])
    for bus, quantity in buses:
        text = [net.bus.loc[bus, 'name']]
        if ikz:
            text.append(f'Ik={net.res_bus_sc.loc[bus, "ikss_ka"]:.2f}кА')
        if voltage:
            text.append(f'V={net.res_bus.loc[bus, "vm_pu"]:.4f}')
        if indexes:
            text.append(f'({bus})')
        _bus(net.bus_geodata.loc[bus, 'x'], net.bus_geodata.loc[bus, 'y'], quantity, text, te)
    for node in nodes:
        text = [net.bus.loc[node, 'name']]
        if ikz:
            text.append(f'Ik={net.res_bus_sc.loc[node, "ikss_ka"]:.2f} кА')
        if voltage:
            text.append(f'V={net.res_bus.loc[node, "vm_pu"]:.4f}')
        if indexes:
            text.append(f'({node})')
        _node(net.bus_geodata.loc[node, 'x'], net.bus_geodata.loc[node, 'y'], text, te)
    #plot lines
    for i, line in net.line.iterrows():
        from_bus = line['from_bus']
        to_bus = line['to_bus']
        text = f'{net.line.loc[i, "std_type"]} {net.line.loc[i, "length_km"]} км'
        parallel = net.line.loc[i, "parallel"]
        if parallel > 1:
            text = f'{parallel}*{text}'
        if line_straight:
            _line_straight(bus_coords[from_bus], bus_coords[to_bus], te=te, text=text)
        else:
            _line(bus_coords[from_bus], bus_coords[to_bus], te=te, text=text)
    #plot ext_grid
    for _, ext_grid in net.ext_grid.iterrows():
        if ext_grid['in_service']:
            x, y = bus_coords[ext_grid['bus']]
            _ext_grid(x, y, te=te)
    #plot trafo
    for _, trafo in net.trafo.iterrows():
        x1, y1 = bus_coords[trafo['hv_bus']]
        x2, y2 = bus_coords[trafo['lv_bus']]
        text = [trafo['name']]
        text.append(trafo['std_type'])
        _trafo(x1, y1, x2, y2, text, te=te)
    #plot trafo3w
    for _, trafo in net.trafo3w.iterrows():
        x1, y1 = bus_coords[trafo['hv_bus']]
        x2, y2 = bus_coords[trafo['mv_bus']]
        x3, y3 = bus_coords[trafo['lv_bus']]
        text = [trafo['name']]
        text.append(trafo['std_type'])
        _trafo3w(x1, y1, x2, y2, x3, y3, text, te=te)
    #plot gen
    for _, gen in net.gen.iterrows():
        x, y = bus_coords[gen['bus']]
        text = [gen['name']]
        text.append(f'{gen['p_mw']}МВт')
        _gen(x, y, text, te=te)
    #plot impedance
    for i, impedance in net.impedance.iterrows():
        from_bus = impedance['from_bus']
        to_bus = impedance['to_bus']
        _impedance(*bus_coords[from_bus], *bus_coords[to_bus], te=te)
