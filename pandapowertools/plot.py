import math

import pandapower as pp
import numpy as np
from textengines.interfaces import *

from pandapowertools.functions import define_c
from pandapowertools.diagram import Diagram




def plot2(net: pp.pandapowerNet, te: TextEngine, isc: bool = True,
          voltage: bool = False, indexes: bool = True,
          length_node: int = 10, length_trafo: int = 6, length_line: int = 20):
    diagram = Diagram(te)
    for bus, bus_coords in net.bus_geodata.iterrows():
        text = [net.bus.loc[bus, 'name']]
        if isc:
            text.append(f'Ik={net.res_bus_sc.loc[bus, "ikss_ka"]:.2f}кА')
        if voltage:
            text.append(f'V={net.res_bus.loc[bus, "vm_pu"]:.4f}')
        if indexes:
            text.append(f'({bus})')
        if bus_coords['coords']:
            diagram.add_bus(index=bus, coords=bus_coords['coords'], text=text,
                            text_coords=(bus_coords['xt'], bus_coords['yt']))
        else:
            diagram.add_node(index=bus, coords=(bus_coords['x'], bus_coords['y']),
                             text=text,
                             text_coords=(bus_coords['xt'], bus_coords['yt']),
                             lenght=length_node,
                             )

    for i, line in net.line.iterrows():
        if line['in_service']:
            from_bus = line['from_bus']
            to_bus = line['to_bus']
            parallel = net.line.loc[i, "parallel"]
            if line['std_type']:
                text = f'{net.line.loc[i, "std_type"]} {net.line.loc[i, "length_km"]} км'
                if parallel > 1:
                    text = f'{parallel}*{text}'
            else:
                l = line['length_km']
                text = f'{line["r_ohm_per_km"] * l / parallel:.3f}+j{line["x_ohm_per_km"] 
                                                                     * l / parallel:.3f} Ом'
            diagram.add_line(index=i, bus1_index=from_bus, bus2_index=to_bus, text=text,
                             lenght=length_line)
    for i, gen in net.gen.iterrows():
        if gen['in_service']:
            text = (gen['name'], f'{gen['p_mw'] * 1000:,.1f}кВт')
            diagram.add_gen(index=i, bus_index=gen['bus'], text=text)

    for i, ext_grid in net.ext_grid.iterrows():
        if ext_grid['in_service']:
            diagram.add_ext_grid(i, ext_grid['bus'])

    for i, switch in net.switch.iterrows():
        diagram.add_switch(index=i, bus_index=switch['bus'], et=switch['et'],
                           element_index=switch['element'],
                           closed=switch['closed'])
    diagram.draw()


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
    for bus, bus_coords in net.bus_geodata.iterrows():
        text = [net.bus.loc[bus, 'name']]
        if ikz:
            text.append(f'Ik={net.res_bus_sc.loc[bus, "ikss_ka"]:.2f}кА')
        if voltage:
            text.append(f'V={net.res_bus.loc[bus, "vm_pu"]:.4f}')
        if indexes:
            text.append(f'({bus})')
        if bus_coords['coords']:
            _bus(bus_coords['coords'], text, te, xt=bus_coords['xt'],
                 yt=bus_coords['yt'])
        else:
            _node(bus_coords['x'], bus_coords['y'], text, te, length_node, bus_coords['xt'],
          bus_coords['yt'])
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
                    elif not from_coords and to_coords:
                        x2 = x1
                        y2 = to_coords[0][1]
                    elif from_coords and to_coords:
                        xb1 = net.bus_geodata.at[from_bus, 'coords'][0][0]
                        xe1 = net.bus_geodata.at[from_bus, 'coords'][1][0]
                        xb2 = net.bus_geodata.at[to_bus, 'coords'][0][0]
                        xe2 = net.bus_geodata.at[to_bus, 'coords'][1][0]
                        coords_sorted = sorted([xb1, xb2, xe1, xe2])
                        x1 = x2 = (coords_sorted[1] + coords_sorted[2]) / 2.0
                        y1 = from_coords[0][1]
                        y2 = to_coords[0][1]
                    else:
                        x1 = net.bus_geodata.at[from_bus, 'x']
                        x2 = net.bus_geodata.at[to_bus, 'x']
                        y1 = net.bus_geodata.at[from_bus, 'y']
                        y2 = net.bus_geodata.at[to_bus, 'y']
                    if line['std_type']:
                        text = f'{net.line.loc[i, "std_type"]} {net.line.loc[i, "length_km"]} км'
                        if parallel > 1:
                            text = f'{parallel}*{text}'
                        if i in net.line_geodata.index:
                            _line(*net.line_geodata.loc[i, 'coords'], te=te, text=text)
                        else:
                            _line_straight((x1, y1), (x2, y2), te=te, text=text)
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
        diagram.add_switch(i, Switch_sym(bus_index, et, element_index, text))
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
