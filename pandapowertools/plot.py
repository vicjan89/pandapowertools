import math

import pandapower as pp
import numpy as np
from textengines.interfaces import *
from pandapowertools.functions import split_str, define_c

dx = 2
r = 0.1
text_size = 0.2

def _node(x, y, text, te: TextEngine, length: int = 8, xt: int | None = None, yt: int | None = None):
    if isinstance(text, str):
        text = [text]
    if xt is None:
        xt = x
    if yt is None:
        yt = y
    te.circle(x, y, r=r, black=False)
    dy = text_size * 1.2
    for t in text:
        if len(t) > length:
            txts = split_str(t, length)
            for txt in txts[::-1]:
                te.label(xt, yt, text=txt, s=text_size, place='ne')
                yt += dy
        else:
            te.label(xt, yt, text=t, s=text_size, place='ne')
            yt += dy


def _bus(coords, text, te: TextEngine, xt: int | None = None, yt: int | None = None): #добавить толщину линии
    if isinstance(text, str):
        text = [text]
    te.lines((coords[0][0], coords[0][1], 0.2, 0.2), (coords[1][0], coords[1][1], 0.2, 0.2))
    te.label(xt-0.3, yt+0.1, text=' '.join(text), place='ne', s=text_size)

def _line_straight(*args, te: TextEngine, text: str = '', length: int = 20):
    if isinstance(text, str):
        text = [text]
    if len(args) == 2:
        (x1, y1), (x2, y2) = args
        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
        middle_x = (x1 + x2) / 2
        middle_y = (y1 + y2) / 2
        te.lines((x1, y1), (x2, y2))
        y = (y1 + y2) / 2
        dx = text_size * 1.2
        x = (x1 + x2) / 2 - r * 5 - dx
        angle = math.atan2(x1-x2, y2-y1)
        angle_degree = math.degrees(angle) + 90
    # for t in text:
    #     te.label(x=(x1+x2)/2 - text_size, y=(y1+y2)/2, s=text_size, place='ne', angle=90, text=t)
    for t in text:
        if len(t) > length:
            txts = split_str(t, length)
            for txt in txts[::-1]:
                x_turned, y_turned = _turn(x, y, middle_x, middle_y, angle)
                te.label(x_turned, y_turned, text=txt, s=text_size, place='c', angle=angle_degree)
                x -= dx
        else:
            te.label(x, y, text=t, s=text_size, place='c', angle=angle_degree)
            x -= dx


def _line(*args, te: TextEngine, text: list[str] | str = '', length: int = 14):
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
    dx = text_size * 1.2
    x = x1 - r * 4
    dy = r * 5
    for t in text:
        if len(t) > length:
            txts = split_str(t, length)
            for txt in txts[::-1]:
                te.label(x, y+dy, text=txt, s=text_size, place='ne', angle=90)
                x -= dx
        else:
            te.label(x, y+dy, text=t, s=text_size, place='ne', angle=90)
            x -= dx

def _turn(x, y, xcenter, ycenter, angle):
    x_res = xcenter + (x - xcenter) * math.cos(angle) - (y - ycenter) * math.sin(angle)
    y_res = ycenter + (x - xcenter) * math.sin(angle) + (y - ycenter) * math.cos(angle)
    return x_res, y_res

def _switch(x, y, angle, te: TextEngine, closed: bool = True, text: str = ''):
    size = r *2
    xlt = xlb = x - size
    xrt = xrb = x + size
    ylt = yrt = y + size
    ylb = yrb = y - size
    coords = []
    for xc, yc in ((xlt, ylt), (xrt, yrt), (xrb, yrb), (xlb, ylb),
                 (x, y + size), (x, y - size),
                 (x - size, y), (x + size, y)):
        coords.append(_turn(xc, yc, x, y, angle))
    te.lines(*coords[:-4], cycle=True)
    if closed:
        te.lines(coords[-2], coords[-1])
    else:
        te.lines(coords[-4], coords[-3])
    return coords[-2:]

def _resistor(x, y, angle, te: TextEngine):
    size_x = r * 1.5
    size_y = r * 3
    xlt = xlb = x - size_x
    xrt = xrb = x + size_x
    ylt = yrt = y + size_y
    ylb = yrb = y - size_y
    coords = []
    for xc, yc in ((xlt, ylt), (xrt, yrt), (xrb, yrb), (xlb, ylb),
                   (x, y + size_y), (x, y - size_y)):
        coords.append(_turn(xc, yc, x, y, angle))
    te.lines(*coords[:-2], cycle=True)
    return coords[-2:]


def _switch_bus(x1, y1, x2, y2, te: TextEngine, closed: bool = False):
    middle_x = (x1 + x2) / 2
    middle_y = (y1 + y2) / 2
    angle = math.atan2(y2-y1, x2-x1)
    coords = _switch(middle_x, middle_y, angle, te, closed)
    te.lines((x1, y1), coords[0])
    te.lines((x2, y2), coords[1])

def _switch_line(x1, y1, x2, y2, te: TextEngine, closed: bool = False):
    length = r * 6
    k = math.sqrt((x2 - x1)**2 + (y2 - y1)**2) / length
    x = x1 + (x2 - x1) / k
    y = y1 + (y2 - y1) / k
    angle = math.atan2(y2-y1, x2-x1)
    _switch(x, y, angle, te, closed)

def _reactor(x1, y1, x2, y2, te: TextEngine, text: list[str] | str = '', length: int = 6):
    x2 = x1
    y2 += r
    y1 -= r
    y_midle = (y1 + y2) / 2
    r_impedance = r * 4
    te.circle(x1, y_midle, r=r_impedance, st_angle=180, en_angle=90, black=False)
    te.lines((x1, y1), (x2, y_midle+r_impedance))
    te.lines((x2, y2), (x1, y_midle), (x1-r_impedance, y_midle))
    if isinstance(text, str):
        text = [text]
    dy = text_size * 1.2
    for t in text:
        if len(t) > length:
            txts = split_str(t, length)
            for txt in txts[::-1]:
                te.label(x1 + r_impedance-r, y_midle, text=txt, place='e', s=text_size)
                y_midle += dy
        else:
            te.label(x1 + r_impedance - r, y_midle, text=t, place='e', s=text_size)
            y_midle += dy

def _impedance(coord1, coord2, te: TextEngine, text: list[str] | str = '', length: int = 20):
    if isinstance(text, str):
        text = [text]
    x1, y1 = coord1
    x2, y2 = coord2
    middle_x = (x1 + x2) / 2
    middle_y = (y1 + y2) / 2
    angle = math.atan2(x1-x2, y2-y1)
    coords = _resistor(middle_x, middle_y, angle, te)
    x1, y1 = _turn(x1, y1 + r, x1, y1, angle)
    x2, y2 = _turn(x2, y2 - r, x2, y2, angle)
    te.lines((x1, y1), coords[1])
    te.lines((x2, y2), coords[0])
    y = (y1 + y2) / 2
    dx = text_size * 1.2
    x = (x1 + x2) / 2 - r * 5 - dx
    angle_degree = math.degrees(angle) + 90
    if 180 <= angle_degree <= 360:
        angle_degree -= 180
    for t in text:
        if len(t) > length:
            txts = split_str(t, length)
            for txt in txts[::-1]:
                x_turned, y_turned = _turn(x, y, middle_x, middle_y, angle)
                te.label(x_turned, y_turned, text=txt, s=text_size, place='c', angle=angle_degree)
                x -= dx
        else:
            te.label(x, y, text=t, s=text_size, place='c', angle=angle_degree)
            x -= dx


def _trafo(x1, y1, x2, y2, text, te: TextEngine, length: int = 6, vector_group: str = ''):
    if y2 > y1:
        x1, y1, x2, y2 = x2, y2, x1, y1
    x1 = x2
    y2 += r
    y1 -= r
    y_midle = (y1 + y2) / 2
    r_trafo = r * 4
    r2 = r * 2
    te.circle(x1, y_midle+r_trafo-r, r=r_trafo, black=False)
    te.circle(x1, y_midle-r_trafo+r, r=r_trafo, black=False)
    te.lines((x1, y1), (x2, y_midle+r_trafo * 2 - r))
    te.lines((x2, y2), (x1, y_midle-r_trafo * 2 + r))
    if vector_group:
        if 'D' in vector_group:
            y = y_midle + r_trafo - r
            te.lines((x1 - r2, y - r), (x1 + r2, y - r), (x1, y + r2), cycle=True)
        if 'd' in vector_group:
            y = y_midle - r_trafo + r
            te.lines((x1 - r2, y - r), (x1 + r2, y - r), (x1, y + r2), cycle=True)
        if 'Y' in vector_group:
            y = y_midle + r_trafo - r
            te.lines((x1, y), (x1, y + r2))
            te.lines((x1, y), (x1 - r2, y - r))
            te.lines((x1, y), (x1 + r2, y - r))
        if 'y' in vector_group:
            y = y_midle - r_trafo + r
            te.lines((x1, y), (x1, y + r2))
            te.lines((x1, y), (x1 - r2, y - r))
            te.lines((x1, y), (x1 + r2, y - r))
        if 'N' in vector_group:
            y = y_midle + r_trafo - r
            te.lines((x1, y), (x1 + r2, y))
        if 'n' in vector_group:
            y = y_midle - r_trafo + r
            te.lines((x1, y), (x1 + r2, y))
    if isinstance(text, str):
        text = [text]
    dy = text_size * 1.2
    for t in text:
        if len(t) > length:
            txts = split_str(t, length)
            for txt in txts[::-1]:
                te.label(x1 + r_trafo-r, y_midle, text=txt, place='e', s=text_size)
                y_midle += dy
        else:
            te.label(x1 + r_trafo - r, y_midle, text=t, place='e', s=text_size)
            y_midle += dy

def _trafo3w(x1, y1, x2, y2, x3, y3, text, te: TextEngine, vector_group: str = ''):
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
    if vector_group:
        w = n = -r_trafo + r
        for letter in vector_group:
            if letter in 'DYN':
                y = y_midle + r_trafo - r
            if letter == 'D':
                    te.lines((x1 - r2, y - r), (x1 + r2, y - r), (x1, y + r2), cycle=True)
            if letter == 'Y':
                te.lines((x1, y), (x1, y + r2))
                te.lines((x1, y), (x1 - r2, y - r))
                te.lines((x1, y), (x1 + r2, y - r))
            if letter == 'N':
                te.lines((x1, y), (x1 + r2, y))
            if letter in 'dyn':
                y = y_midle - r_trafo + r
            if letter == 'd':
                if w > 0 and n < 0:
                    n = -n
                te.lines((x1 - r2 + w, y - r), (x1 + r2 + w, y - r), (x1 + w, y + r2), cycle=True)
                w = -w
            if letter == 'y':
                if w > 0 and n < 0:
                    n = -n
                te.lines((x1 + w, y), (x1 + w, y + r2))
                te.lines((x1 + w, y), (x1 - r2 + w, y - r))
                te.lines((x1 + w, y), (x1 + r2 + w, y - r))
                w = -w
            if letter == 'n':
                te.lines((x1 + n, y), (x1 + r2 + n, y))
                n = -n
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

def _capacitor(x, y, text, te: TextEngine):
    d = r * 7
    w = r * 5
    w2 = r * 2
    te.lines((x, y-r), (x, y-d))
    te.lines((x, y-d-r-d), (x, y-d-r))
    te.lines((x-w, y-d), (x+w, y-d))
    te.lines((x-w, y-d-r), (x+w, y-d-r))
    # _ground(x, y - d - d, te)
    dy = text_size * 1.2
    for t in text:
        te.label(x + w2, y - r, text=t, place='e', s=text_size)
        y -= dy

def _ground(x, y, te: TextEngine):
    w1 = r * 3
    w2 = r * 2
    w3 = r
    te.lines((x-w1, y), (x+w1, y))
    te.lines((x-w2, y-r), (x+w2, y-r))
    te.lines((x-w3, y-r*2), (x+w3, y-r*2))


def plot(net: pp.pandapowerNet, te: TextEngine, indexes: bool = True, ikz: bool = False,
         voltage: bool = False, impedance: bool = False, length_node: int = 8, length_trafo: int = 6, length: int = 20):
    '''
    Plot pandapowerNet to TextEngine format
    :param net:
    :param te:
    :param indexes: if True then plot inexes
    :param length_node: length of text row
    :param length_trafo: length of text row
    :return:
    '''
    #plot buses
    bus_coords = {}
    for bus, bus_coords in net.bus_geodata.iterrows():
        text = [net.bus.loc[bus, 'name']]
        if ikz:
            text.append(f'Ik={net.res_bus_sc.loc[bus, "ikss_ka"]:.2f}кА')
        if voltage:
            text.append(f'V={net.res_bus.loc[bus, "vm_pu"]:.4f}')
        if indexes:
            text.append(f'({bus})')
        if bus_coords['coords']:
            _bus(bus_coords['coords'], text, te, xt=bus_coords['xt'], yt=bus_coords['yt'])
        else:
            _node(bus_coords['x'], bus_coords['y'], text, te, length_node, bus_coords['xt'], bus_coords['yt'])
    #plot lines
    for i, line in net.line.iterrows():
        if line['in_service']:
            from_bus = line['from_bus']
            to_bus = line['to_bus']
            if (from_bus in net.bus_geodata.index and to_bus in net.bus_geodata.index) or i in net.line_geodata.index:
                parallel = net.line.loc[i, "parallel"]
                x1, y1 = net.bus_geodata.loc[from_bus, ['x', 'y']]
                x2, y2 = net.bus_geodata.loc[to_bus, ['x', 'y']]
                if impedance:
                    l = line['length_km']
                    text = f'{line["r_ohm_per_km"] * l / parallel:.3f}+j{line["x_ohm_per_km"] * l / parallel:.3f} Ом'
                    _impedance((x1, y1), (x2, y2), te, text, length)
                else:
                    from_coords = net.bus_geodata.at[from_bus, 'coords']
                    to_coords = net.bus_geodata.at[to_bus, 'coords']
                    if from_coords and not to_coords:
                        x1 = x2
                        y1 = from_coords[0][1]
                    if not from_coords and to_coords:
                        x2 = x1
                        y2 = to_coords[0][1]
                    if from_coords and to_coords:
                        xb1 = net.bus_geodata.at[from_bus, 'coords'][0][0]
                        xe1 = net.bus_geodata.at[from_bus, 'coords'][1][0]
                        xb2 = net.bus_geodata.at[to_bus, 'coords'][0][0]
                        xe2 = net.bus_geodata.at[to_bus, 'coords'][1][0]
                        coords_sorted = sorted([xb1, xb2, xe1, xe2])
                        x1 = x2 = (coords_sorted[1] + coords_sorted[2]) / 2.0
                        y1 = from_coords[0][1]
                        y2 = to_coords[0][1]
                    if line['std_type']:
                        text = f'{net.line.loc[i, "std_type"]} {net.line.loc[i, "length_km"]} км'
                        if parallel > 1:
                            text = f'{parallel}*{text}'
                        if i in net.line_geodata.index:
                            _line(*net.line_geodata.loc[i, 'coords'], te=te, text=text)
                        else:
                            _line((x1, y1), (x2, y2), te=te, text=text)
                    else:
                        l = line['length_km']
                        text = f'{line["r_ohm_per_km"] * l / parallel:.3f}+j{line["x_ohm_per_km"] * l / parallel:.3f} Ом'
                        _reactor(x1, y1, x2, y2, te=te, text=text, length=length_trafo)
    #plot ext_grid
    for _, ext_grid in net.ext_grid.iterrows():
        if ext_grid['in_service'] and ext_grid['bus'] in net.bus_geodata.index:
            x, y = net.bus_geodata.loc[ext_grid['bus'], ['x', 'y']]
            if impedance:
                name = ext_grid['name']
                if name is None:
                    name = ''
                text = [name]
                u_bus = net.bus.at[ext_grid['bus'], 'vn_kv']
                i_kz_max = ext_grid['s_sc_max_mva'] / u_bus / math.sqrt(3)
                zs = define_c(u_bus, "max", 10) * u_bus / i_kz_max / math.sqrt(3)
                rx = ext_grid['rx_max']
                xs = math.sqrt(zs ** 2 / (1 + rx))
                rs = rx * xs
                text.append(f'Zmax={rs:.3f}+j{xs:.3f} = {zs:.3f} Ом')
                i_kz_min = ext_grid['s_sc_min_mva'] / u_bus / math.sqrt(3)
                zs = define_c(u_bus, "min", 10) * u_bus / i_kz_min / math.sqrt(3)
                rx = ext_grid['rx_min']
                xs = math.sqrt(zs ** 2 / (1 + rx))
                rs = rx * xs
                text.append(f'Zmin={rs:.3f}+j{xs:.3f} = {zs:.3f} Ом')
                _impedance((x, y), (x, y + 2), te, text, length=length)
                _ext_grid(x, y + 2 - r -r, te=te)
            else:
                _ext_grid(x, y, te=te)
    #plot trafo
    for _, trafo in net.trafo.iterrows():
        hv_bus = trafo['hv_bus']
        lv_bus = trafo['lv_bus']
        if hv_bus in net.bus_geodata.index and lv_bus in net.bus_geodata.index:
            x1, y1 = net.bus_geodata.loc[hv_bus, ['x', 'y']]
            x2, y2 = net.bus_geodata.loc[lv_bus, ['x', 'y']]
            if impedance:
                ukx = math.sqrt(trafo['vk_percent'] ** 2 - trafo['vkr_percent'] ** 2)
                kt = 0.95 * 1.1 / (1 + 0.6 * ukx / 100)
                zt = trafo['vk_percent'] * trafo['vn_hv_kv'] ** 2 / 100 / trafo['sn_mva'] / kt
                rt = kt * trafo['vkr_percent'] * trafo['vn_hv_kv'] ** 2 / 100 / trafo['sn_mva']
                xt = math.sqrt(zt ** 2 - rt ** 2)
                text = f'{rt:.3f}+j{xt:.3f} Ом'
                _impedance((x1, y1), (x2, y2), te=te, text=text, length=length_trafo)
            else:
                text = [trafo['name']]
                text.append(trafo['std_type'])
                vector_group = ''
                if 'vector_group' in trafo:
                    vector_group = trafo['vector_group']
                _trafo(x1, y1, x2, y2, text, te=te, length=length_trafo, vector_group=vector_group)
    #plot trafo3w
    for _, trafo in net.trafo3w.iterrows():
        hv_bus = trafo['hv_bus']
        mv_bus = trafo['mv_bus']
        lv_bus = trafo['lv_bus']
        if all(bus in net.bus_geodata.index for bus in [hv_bus, mv_bus, lv_bus]):
            x1, y1 = net.bus_geodata.loc[hv_bus, ['x', 'y']]
            x2, y2 = net.bus_geodata.loc[mv_bus, ['x', 'y']]
            x3, y3 = net.bus_geodata.loc[lv_bus, ['x', 'y']]
            text = [trafo['name']]
            text.append(trafo['std_type'])
            vector_group = ''
            if 'vector_group' in trafo:
                vector_group = trafo['vector_group']
            _trafo3w(x1, y1, x2, y2, x3, y3, text, te=te, vector_group=vector_group)
    #plot gen
    for _, gen in net.gen.iterrows():
        bus = gen['bus']
        if bus in net.bus_geodata.index:
            x, y = net.bus_geodata.loc[bus, ['x', 'y']]
            text = [gen['name']]
            text.append(f'{gen['p_mw']}МВт')
            _gen(x, y, text, te=te)
    #plot impedance
    for i, impedance in net.impedance.iterrows():
        from_bus = impedance['from_bus']
        to_bus = impedance['to_bus']
        if from_bus in net.bus_geodata.index and to_bus in net.bus_geodata.index:
            _reactor(*net.bus_geodata.at[from_bus, ['x', 'y']], *net.bus_geodata.at[to_bus, ['x', 'y']], te=te)
    #plot switch
    for i, switch in net.switch.iterrows():
        bus = switch['bus']
        if bus in net.bus_geodata.index:
            element = switch['element']
            et = switch['et']
            x1 = net.bus_geodata.at[bus, 'x']
            y1 = net.bus_geodata.at[bus, 'y']
            match et:
                case 'b':
                    if element in net.bus_geodata.index:
                        bus_coords1 = [(x1, y1)]
                        if net.bus_geodata.at[bus, 'coords']:
                            bus_coords1.extend(net.bus_geodata.at[bus, 'coords'])
                        x2 = net.bus_geodata.at[element, 'x']
                        y2 = net.bus_geodata.at[element, 'y']
                        bus_coords2 = [(x2, y2)]
                        if net.bus_geodata.at[element, 'coords']:
                            bus_coords2.extend(net.bus_geodata.at[element, 'coords'])
                        nearby_coords = None
                        length_min = None
                        for c1 in bus_coords1:
                            for c2 in bus_coords2:
                                length = math.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2)
                                if length_min:
                                    if length < length_min:
                                        length_min = length
                                        nearby_coords = c1, c2
                                else:
                                    length_min = length
                        (x1, y1), (x2, y2) = nearby_coords
                        _switch_bus(x1, y1, x2, y2, te=te, closed=switch['closed'])
                case 'l':
                    bus2 = net.line.at[element, 'from_bus'] if bus == net.line.at[element, 'to_bus'] else net.line.at[element, 'to_bus']
                    if bus2 in net.bus_geodata.index:
                        x2 = net.bus_geodata.at[bus2, 'x']
                        y2 = net.bus_geodata.at[bus2, 'y']
                        _switch_line(x1, y1, x2, y2, te=te, closed=switch['closed'])

    #plot shunt
    for _, shunt in net.shunt.iterrows():
        bus = shunt['bus']
        if shunt['in_service'] and bus in net.bus_geodata.index:
            x, y = net.bus_geodata.loc[bus, ['x', 'y']]
            v = net.bus.at[shunt['bus'], 'vn_kv']
            p_mw = shunt['p_mw']
            if np.isnan(p_mw):
                rc = 0
            else:
                rc = v ** 2 / shunt['p_mw']
            xc = v ** 2 / shunt['q_mvar']
            sign = '+'
            capacitor = False
            if xc < 0:
                xc = -xc
                sign = '-'
                capacitor = True
            rc_str = f'{rc:.1f}' if rc < 9999 else f'{rc:.4e}'
            xc_str = f'{xc:.1f}' if xc < 9999 else f'{xc:.4e}'
            name = shunt['name']
            if name is None:
                name = ''
            else:
                name += ' '
            text = [f'{name}{rc_str}{sign}j{xc_str}']
            if capacitor:
                _capacitor(x, y, text, te=te)
            else:
                _impedance((x, y), (x, y - r * 11), te=te, text=text, length=length)
                _ground(x, y - r * 10, te=te)
