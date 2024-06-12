import math

import numpy as np

from matplotlib.font_manager import FontProperties
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.pyplot import savefig

import pandapower.plotting as plot

from matplotlib.patches import Circle

def plot_ikz(net, collections_data, text_size: float = 0.05, fault_1ph=False, case='max', lv_tol_percent=10):
    #шины
    buses_ikz = []
    for n in collections_data['buses']:
        text = ''
        if not math.isnan(net.res_bus_sc.at[n, "ikss_ka"]):
            if n == 42:
                text += ''
            else:
                ikz = net.res_bus_sc.at[n, "ikss_ka"] * 1000
                text += f' {ikz:.0f}А'
                if fault_1ph and net.bus.at[n, "vn_kv"] == 0.4:
                    text += f'({ikz/25/1.732:.0f}A)'
        buses_ikz.append(text)

    coords_ikz = [(x, y + text_size) for x, y in collections_data['coords_buses']]
    collections_data['collections'].append(create_annotation(text_size, buses_ikz, coords_ikz))



    #трансформаторы
    trafos_Uk = []
    for i in  collections_data['trafos']:
        t = net.trafo
        trafos_Uk.append(f'Uk={t.at[i, "vk_percent"]}%,Ukr={t.at[i, "vkr_percent"]}%')
    collections_data['collections'].append(create_annotation_shift(trafos_Uk, collections_data['coords_trafos'],
                                                          0.03, 2 * text_size, text_size))

    trafos_r_x = []
    for i in collections_data['trafos']:
        t = net.trafo
        vk = t.at[i,"vk_percent"] / 100
        vkr = t.at[i,"vkr_percent"] / 100
        vn_lv_kv = t.at[i,"vn_lv_kv"]
        vn = vn_lv_kv if vn_lv_kv == 11 else t.at[i,"vn_hv_kv"]
        z = vk * (vn ** 2) / t.at[i,"sn_mva"]
        r = vkr * (vn ** 2) / t.at[i,"sn_mva"]
        x = (z ** 2 - r ** 2) ** 0.5
        vkx = math.sqrt(vk**2-vkr**2)
        _, cmax = define_c(vn_lv_kv, case, lv_tol_percent)
        kt = 0.95*cmax/(1+0.6*vkx)
        trafos_r_x.append(f'{r*kt:.3f}+j{x*kt:.3f} Ом')
    collections_data['collections'].append(create_annotation_shift(trafos_r_x, collections_data['coords_trafos'],
                                                                   0.03, text_size, text_size))

    #трансформаторы трёхобмоточные
    trafos3w_Uk = []
    for i in collections_data['trafos3w']:
        t = net.trafo3w
        trafos3w_Uk.append(f'UkВС={t.at[i,"vk_hv_percent"]}%,UkСН={t.at[i,"vk_mv_percent"]}%,UkВН={t.at[i,"vk_lv_percent"]}%')

    collections_data['collections'].append(create_annotation_shift(trafos3w_Uk, collections_data['coords_trafos3w'],
                                                          0.03, -4 * text_size, text_size))
    trafos3w_Uk = []
    for i in collections_data['trafos3w']:
        t = net.trafo3w
        trafos3w_Uk.append(f'UkrВС={t.at[i,"vkr_hv_percent"]}%,UkrСН={t.at[i,"vkr_mv_percent"]}%,UkrВН={t.at[i,"vkr_lv_percent"]}%')

    collections_data['collections'].append(create_annotation_shift(trafos3w_Uk, collections_data['coords_trafos3w'],
                                                          0.03, -5 * text_size, text_size))

    trafos3w_r_x = []
    for i in collections_data['trafos3w']:
        t = net.trafo3w
        vk = t.at[i, "vk_lv_percent"] / 100
        vkr = t.at[i, "vkr_lv_percent"] / 100
        vn_lv_kv = t.at[i, "vn_lv_kv"]
        z = vk * (vn_lv_kv ** 2) / t.at[i, "sn_hv_mva"]
        r = vkr * (vn_lv_kv ** 2) / t.at[i, "sn_hv_mva"]
        x = (z ** 2 - r ** 2) ** 0.5
        vkx = math.sqrt(vk ** 2 - vkr ** 2)
        _, cmax = define_c(vn_lv_kv, case, lv_tol_percent)
        kt = 0.95 * cmax / (1 + 0.6 * vkx)
        trafos3w_r_x.append(f'          {r*kt:.3f}+j{x*kt:.3f} Ом')
    collections_data['collections'].append(create_annotation_shift(trafos3w_r_x, collections_data['coords_trafos3w'],
                                                                   0.03, -2 * text_size, text_size))


    # вывод удельных сопротивлений
    coords = calc_coords_annotation(collections_data['coords_lines'], 2, 0.08)
    line_names = [f'{net.std_types["line"][net.line.loc[line].std_type]["r_ohm_per_km"]: .3f}' \
                  f'+j{net.std_types["line"][net.line.loc[line].std_type]["x_ohm_per_km"]: .3f} Ом/км' for line in
                  collections_data['lines']]
    collections_data['collections'].append(create_annotation(size=text_size, texts=line_names, coords=coords))


    # вывод сопротивлений
    coords = calc_coords_annotation(collections_data['coords_lines'], 3, 0.08)
    line_names = [
        f'{net.std_types["line"][net.line.loc[line].std_type]["r_ohm_per_km"] * net.line.loc[line].length_km: .3f}' \
        f'+j{net.std_types["line"][net.line.loc[line].std_type]["x_ohm_per_km"] * net.line.loc[line].length_km: .3f} Ом'
        for line in
        collections_data['lines']]
    collections_data['collections'].append(create_annotation(size=text_size, texts=line_names, coords=coords))


def create_annotation(size: float, texts: list, coords: list[tuple]):
    '''
    Создаёт подписи элементов с определённым форматированием
    :param size: размер текста
    :param texts: список строк для подписей
    :param coords: список координат вида [(x1, y1), ..., (xn, yn)]
    :return: коллекция аннтотаций Matplotlib
    '''
    return plot.create_annotation_collection(size=size, texts=texts,
                                               coords=coords, zorder=3,
                                               color='k', prop=FontProperties(style='italic'), linewidths=0.3)
def create_annotation_shift(names, coords, dx, dy, text_size=0.05):
    coords_shift = [(coord[0] + dx, coord[1] + dy) for coord in coords]
    return create_annotation(size=text_size, texts=names, coords=coords_shift)

def shift_coords_buses(net, buses: tuple, dx: int, dy: int, grid: tuple):
    '''
    Сдвигает координаты шин на указанные величины путём прибавления dx и dy к соответствующим координатам
    :param buses: список индексов шин для сдвига
    :param dx: сдвиг по оси x
    :param dy: сдвиг по оси y
    :return: None
    '''
    x_grid, y_grid = grid
    net.bus_geodata.x.loc[buses] += dx * x_grid
    net.bus_geodata.y.loc[buses] += dy * y_grid

def coords_buses_by_grid(net, buses: tuple = None, grid: tuple = (0 ,0)):
    '''
    Сдвигает координаты шин смещая их к узлам сетки с расстояниями между узлами dx и dy
    :param buses: список индексов шин для сдвига
    :param dx: шаг сетки по оси x
    :param dy: шаг сетки по оси y
    :return: None
    '''
    if not buses:
        buses = net.bus.index.tolist()
    dx, dy = grid
    net.bus_geodata.x.loc[buses] = net.bus_geodata.x.loc[buses].apply(lambda x: int(x/dx) * dx if (x/dx-int(x/dx)) < 0.5 else (int(x/dx) + 1) * dx)
    net.bus_geodata.y.loc[buses] = net.bus_geodata.y.loc[buses].apply(lambda y: int(y/dy) * dy if (y/dy-int(y/dy)) < 0.5 else (int(y/dy) + 1) * dy)


def calc_coords_annotation(coords: list[tuple], num_row, text_size) -> list:
    '''
    Рассчитывает координаты для текстовых подписей линий
    :param coords: список координат линий в формате кортежа (x1, y1, x2, y2)
    :param num_row: номер строки подписи
    :param text_size: размер шрифта по высоте
    :return: список координат для подписей в формате (x, y)
    '''
    res_coords = []
    for x1, y1, x2, y2 in coords:
        dx = x1 - x2
        dy = y1 - y2
        if dy > text_size and abs(dx/dy) < 4:
            ddy = num_row * text_size
            ddx = ddy/dy*dx
            x = x1 - dx * 0.55 - ddx + 0.01
            y = y1 - dy * 0.55 - ddy
            if dx > 0:
                x += text_size
            elif dx == 0:
                x += 0.01
        else:
            x = x1 - dx / 2
            y = y1 - dy / 2 - num_row * text_size
        res_coords.append((x, y))
    return res_coords

def trafo_patches(coords, size, color, linewidths):
    """
    Создаёт коллекцию окружностей и линий для трёхобмоточного трансформатора

    :param coords: list of connecting node coordinates (usually should be \
        `[((x11, y11), (x12, y12)), ((x21, y21), (x22, y22)), ...]`)
    :type coords: (N, (2, 2)) shaped iterable
    :param size: size of the trafo patches
    :type size: float
    :param kwargs: additional keyword arguments (might contain parameters "patch_edgecolor" and\
        "patch_facecolor")
    :type kwargs:
    :return: Return values are: \
        - lines (list) - list of coordinates for lines connecting nodes and transformer patches\
        - circles (list of Circle) - list containing the transformer patches (rings)
    """

    circles, lines = list(), list()
    for i, (p1, p2, p3) in enumerate(coords):
        p1 = np.array(p1)
        p2 = np.array(p2)
        p3 = np.array(p3)
        if np.all(p1 == p2):
            continue
        d = np.sqrt(np.sum((p1 - p2) ** 2))
        if size is None:
            size_this = np.sqrt(d) / 5
        else:
            size_this = size
        off = size_this * 0.35
        circ1 = (0.5 - off / d) * (p1 - p2) + p2
        circ2 = (0.5 + off / d) * (p1 - p2) + p2
        circ3 = (p1 - p2)/2 + p2
        circ3[0] += off*2
        circles.append(Circle(circ1, size_this))
        circles.append(Circle(circ2, size_this))
        circles.append(Circle(circ3, size_this))
        lp1 = (0.5 - off / d - size_this / d) * (p2 - p1) + p1
        lp2 = (0.5 - off / d - size_this / d) * (p1 - p2) + p2
        lp3 = (circ3[0]+size_this, circ3[1])
        lines.append([p1, lp1])
        lines.append([p2, lp2])
        lines.append([p3, lp3])
    return lines, circles

def create_trafo3w_collection(net, trafo3ws=None, color='black', linewidths=1, linestyle='-', size=0.05):
    '''
    Переписан с реализации PandaPower для корректного отображения
    :param net:
    :param trafo3ws:
    '''
    coords = []
    for trafo in trafo3ws:
        coords.append(((net.bus_geodata.x.loc[net.trafo3w.hv_bus.loc[trafo]], net.bus_geodata.y.loc[net.trafo3w.hv_bus.loc[trafo]]),
                  (net.bus_geodata.x.loc[net.trafo3w.lv_bus.loc[trafo]], net.bus_geodata.y.loc[net.trafo3w.lv_bus.loc[trafo]]),
                   (net.bus_geodata.x.loc[net.trafo3w.mv_bus.loc[trafo]], net.bus_geodata.y.loc[net.trafo3w.mv_bus.loc[trafo]])))

    lines, circles = trafo_patches(coords, size, color, linewidths)

    lc = LineCollection(lines)
    pc = PatchCollection(circles)
    lc.set(color=color, linewidths=linewidths, linestyle=linestyle)
    pc.set(edgecolor=color, facecolor='none', linewidths=linewidths, linestyle=linestyle)

    return lc, pc

def plot_net(net, index=False, generic_coordinates=False, text_size: float = 0.05, draw_trafos: bool = True,
             scaleX: float = 1.0, scaleY: float = 1.0, rotate: bool = False, mirror: bool = False):
    collections_data = dict()
    collections_data['collections'] = []
    collections_data['coords_trafos'] = []
    collections_data['coords_trafos3w'] = []

    if generic_coordinates:
        plot.create_generic_coordinates(net, overwrite=True)
        # set scale
        if scaleX != 1:
            net.bus_geodata.x = net.bus_geodata.x.apply(lambda x: x * scaleX)
        if scaleY != 1:
            net.bus_geodata.y = net.bus_geodata.y.apply(lambda y: y * scaleY)
        if rotate:
            temp = net.bus_geodata.y
            net.bus_geodata.y = net.bus_geodata.x
            net.bus_geodata.x = temp
        if mirror:
            net.bus_geodata.y = net.bus_geodata.y.apply(lambda y: -y)
        with open('coords.yaml', 'w', encoding='utf-8') as file:
            for i, b in net.bus_geodata.iterrows():
                file.write(f'      geodata:\n        - {b.x}\n        - {b.y}\n')

    # вывод шин которые в работе
    collections_data['buses'] = [bus for bus in net.bus.index.tolist() if net.bus.in_service.loc[bus]]
    collections_data['collections'].append(plot.create_bus_collection(net, buses=collections_data['buses'], size=0.02, color='k'))

    # вывод подписей шин
    buses_name = []
    for n, b in net.bus.loc[collections_data['buses']].iterrows():
        text = ''
        if index:
            text += f'({n})'
        text += f'{b.at["name"]}'
        buses_name.append(text)

    collections_data['coords_buses'] = list(map(lambda coord: (coord[0]-0.0, coord[1]+0.07),
                                                zip(net.bus_geodata.x.loc[collections_data['buses']].values,
                                                    net.bus_geodata.y.loc[collections_data['buses']].values)))
    collections_data['collections'].append(plot.create_annotation_collection(size=text_size, texts=buses_name,
                                                                             coords=collections_data['coords_buses'], zorder=3,
                                                                             color='k', prop=FontProperties(style='italic'), linewidths=0.04))


    if draw_trafos:
        # сделаем x шины hv трансформаторов равной x шины lv
        bus_geodata = net["bus_geodata"].copy(deep=True)
        # trafos_index = net.trafo.index
        # for trafo in trafos_index[::-1]:
        #     bus_geodata.x.loc[net.trafo.hv_bus.loc[trafo]] = bus_geodata.x.loc[net.trafo.lv_bus.loc[trafo]]
        # trafos_index = net.trafo3w.index
        # for trafo in trafos_index[::-1]:
        #     bus_geodata.x.loc[net.trafo3w.hv_bus.loc[trafo]] = bus_geodata.x.loc[net.trafo3w.lv_bus.loc[trafo]]

        trafos_mark = []
        trafos_name = []
        # вывод трансформаторов в работе
        trafos_index_in_service = net.trafo.loc[net.trafo['in_service']]
        collections_data['trafos'] = trafos_index_in_service.index.tolist()
        if len(trafos_index_in_service):
            tr_in_service = plot.create_trafo_collection(net, trafos=trafos_index_in_service.index, size=0.05, linewidths=0.4,
                                                         bus_geodata=bus_geodata)
            collections_data['collections'].append(tr_in_service)
            circles = tr_in_service[0].get_paths()

            collections_data['coords_trafos'].extend([(coord.vertices[0][0], coord.vertices[0][1] + 0.06) for coord in
                                                      circles[::2]])

            trafos_name.extend([f'{t.at["name"]}' for n, t in trafos_index_in_service.iterrows()])

            trafos_mark.extend([f'{t.at["std_type"]}' for n, t in trafos_index_in_service.iterrows()])

        # вывод трансформаторов выведенных из работы
        trafos_index_not_in_service = net.trafo.loc[net.trafo['in_service'] == False]
        collections_data['trafos'].extend(trafos_index_not_in_service.index.tolist())
        if len(trafos_index_not_in_service):
            tr_not_in_service = plot.create_trafo_collection(net, trafos=trafos_index_not_in_service.index, size=0.05,
                                                             linewidths=0.4, linestyle='--', bus_geodata=bus_geodata)
            collections_data['collections'].append(tr_not_in_service)
            circles = tr_not_in_service[0].get_paths()
            collections_data['coords_trafos'].extend([(coord.vertices[0][0], coord.vertices[0][1] + 0.06) for coord in
                                                      circles[::2]])

            trafos_name.extend([f'{t.at["name"]}' for n, t in trafos_index_not_in_service.iterrows()])

            trafos_mark.extend([f'{t.at["std_type"]}' for n, t in trafos_index_not_in_service.iterrows()])

        if trafos_mark:
            collections_data['collections'].append(create_annotation_shift(trafos_mark, collections_data['coords_trafos'],
                                                                           0.03, 3 * text_size, text_size))
        if trafos_name:
            collections_data['collections'].append(create_annotation_shift(trafos_name, collections_data['coords_trafos'],
                                                                           0.03, 4 * text_size, text_size))

        trafos3w_name =[]
        trafos3w_mark = []
        # вывод трёхобмоточных трансформаторов в работе
        trafos_index_in_service = net.trafo3w.loc[net.trafo3w['in_service']]
        collections_data['trafos3w'] = trafos_index_in_service.index.tolist()
        if len(trafos_index_in_service):
            tr3w_in_service = create_trafo3w_collection(net, trafo3ws=trafos_index_in_service.index, size=0.05)

            collections_data['collections'].append(tr3w_in_service)

            circles = tr3w_in_service[0].get_paths()
            collections_data['coords_trafos3w'].extend([(coord.vertices[0][0], coord.vertices[0][1] + 0.06) for coord in
                                                        circles[::3]])

            trafos3w_name.extend([f'{t.at["name"]}' for n, t in trafos_index_in_service.iterrows()])
            trafos3w_mark.extend([f'{t.at["std_type"]}' for n, t in trafos_index_in_service.iterrows()])

        # вывод трёхобмоточных трансформаторов выведенных из работы
        trafos_index_not_in_service = net.trafo3w.loc[net.trafo3w['in_service'] == False]
        collections_data['trafos3w'].extend(trafos_index_not_in_service.index.tolist())
        if len(trafos_index_not_in_service):
            tr3w_not_in_service = create_trafo3w_collection(net, trafo3ws=trafos_index_not_in_service.index, size=0.05, linestyle='--')

            collections_data['collections'].append(tr3w_not_in_service)

            circles = tr3w_not_in_service[0].get_paths()
            collections_data['coords_trafos3w'].extend([(coord.vertices[0][0], coord.vertices[0][1] + 0.06) for coord in
                                                        circles[::3]])

            trafos3w_name.extend([f'{t.at["name"]}' for n, t in trafos_index_not_in_service.iterrows()])
            trafos3w_mark.extend([f'{t.at["std_type"]}' for n, t in trafos_index_not_in_service.iterrows()])

        collections_data['collections'].append(create_annotation_shift(trafos3w_name, collections_data['coords_trafos3w'],
                                                                       0.03, -2*text_size, text_size))

        collections_data['collections'].append(create_annotation_shift(trafos3w_mark, collections_data['coords_trafos3w'],
                                                                       0.03, -3*text_size, text_size))


    # вывод сборных шин
    # bbc = plot.create_busbar_collection(net, buses=[0,1,2,3,4,5,6,7,8], color='k', linewidth=3)
    # collections_data['collections'].append(bbc)


    # вывод линий
    lines_not_in_service = set([line for line in net.line.index.tolist() if net.line.in_service.loc[line] == False])
    lines_with_geo = set(net.line_geodata.index.tolist()) - lines_not_in_service
    lines_without_geo = list(set(net.line.index.tolist()) - lines_not_in_service - lines_with_geo)
    lines_with_geo = list(lines_with_geo)
    collections_data['lines'] = lines_without_geo + lines_with_geo

    lc = plot.create_line_collection(net, color='k', lines=lines_without_geo, linewidths=0.3, use_bus_geodata=True)
    lc_with_geo = plot.create_line_collection(net, lines=lines_with_geo, color='k', linewidths=0.3,
                                              use_bus_geodata=False)
    paths_lines = lc.get_paths() if lc else []
    paths_lines.extend(lc_with_geo.get_paths() if lc_with_geo else [])


    collections_data['coords_lines'] = [(line.vertices[0][0], line.vertices[0][1], line.vertices[1][0],
                                         line.vertices[1][1]) for line in paths_lines]
    # вывод марки кабеля/провода
    line_names = []
    for line in collections_data['lines']:
        text = '  '
        if index:
            text += f'({line}) '
        text += f'{net.line.loc[line].std_type}'
        line_names.append(text)
    coords = calc_coords_annotation(collections_data['coords_lines'], 0, text_size)
    collections_data['collections'].append(create_annotation(size=text_size, texts=line_names,
                                                             coords=coords))
    # вывод длины кабеля/провода
    line_names = []
    for line in collections_data['lines']:
        text = f'{net.line.loc[line].length_km}км'
        line_names.append(text)
    coords = calc_coords_annotation(collections_data['coords_lines'], 1, text_size)
    collections_data['collections'].append(create_annotation(size=text_size, texts=line_names,
                                                             coords=coords))

    # вывод секционных выключателей
    switches, helper_lines = plot.create_bus_bus_switch_collection(net, size=0.1, helper_line_size=2,
                                                                   helper_line_color='k',
                                                                   helper_line_style='-')
    helper_lines.set_zorder(0)
    helper_lines.set_linewidth(1)
    collections_data['collections'].extend([lc, lc_with_geo, (switches, helper_lines)])

    # вывод выключателей
    switches = plot.create_line_switch_collection(net, size=0.1, distance_to_bus=0.5, use_line_geodata=True)
    switches.set_zorder(2)
    collections_data['collections'].append(switches)

    return collections_data

def plot_buses(net, collections_data):
    # вывод шин которые в работе
    collections_data['buses'] = [bus for bus in net.bus.index.tolist() if net.bus.in_service.loc[bus]]
    collections_data['collections'].append(plot.create_bus_collection(net, buses=collections_data['buses'], size=0.02, color='k'))

    # вывод подписей шин
    buses_name = []
    for n, b in net.bus.loc[collections_data['buses']].iterrows():
        text = ''
        if index:
            text += f'({n})'
        text += f'{b.at["name"]}'
        buses_name.append(text)

    collections_data['coords_buses'] = list(map(lambda coord: (coord[0]-0.0, coord[1]+0.07),
                                                zip(net.bus_geodata.x.loc[collections_data['buses']].values,
                                                    net.bus_geodata.y.loc[collections_data['buses']].values)))
    collections_data['collections'].append(plot.create_annotation_collection(size=text_size, texts=buses_name,
                                                                             coords=collections_data['coords_buses'], zorder=3,
                                                                             color='k', prop=FontProperties(style='italic'), linewidths=0.04))
    return collections_data

def create_resistor_collection(net):
    # if not MATPLOTLIB_INSTALLED:
    #     soft_dependency_error(str(sys._getframe().f_code.co_name) + "()", "matplotlib")
    #
    # impedances =  net.trafos.index
    # if len(impedances) == 0:
    #     return None
    #
    # coords, impedances_with_geo = coords_from_node_geodata(
    #     impedances, net.impedance.from_bus.loc[impedances].values,
    #     net.impedance.to_bus.loc[impedances].values,
    #     bus_geodata if bus_geodata is not None else net["bus_geodata"], "impedance")
    #
    # if len(impedances_with_geo) == 0:
    #     return None
    #
    # infos = [infofunc(imp) for imp in impedances_with_geo] if infofunc else []
    #
    # lc = _create_line2d_collection(coords, impedances_with_geo, infos=infos, picker=picker,
    #                                **kwargs)
    #
    # return lc
    ...

def plot_equivalent_circuit(net):
    collections_data = dict()
    collections_data['collections'] = []
    collections_data['coords_trafos'] = []
    collections_data['coords_trafos3w'] = []

    # вывод шин которые в работе
    plot_buses(net, collections_data)

    if draw_trafos:
        trafos_mark = []
        trafos_name = []
        # вывод трансформаторов в работе
        trafos_index_in_service = net.trafo.loc[net.trafo['in_service']]
        collections_data['trafos'] = trafos_index_in_service.index.tolist()
        if len(trafos_index_in_service):
            tr_in_service = plot.create_trafo_collection(net, trafos=trafos_index_in_service.index, size=0.05, linewidths=0.4,
                                                         bus_geodata=bus_geodata)
            collections_data['collections'].append(tr_in_service)
            circles = tr_in_service[0].get_paths()

            collections_data['coords_trafos'].extend([(coord.vertices[0][0], coord.vertices[0][1] + 0.06) for coord in
                                                      circles[::2]])

            trafos_name.extend([f'{t.at["name"]}' for n, t in trafos_index_in_service.iterrows()])

            trafos_mark.extend([f'{t.at["std_type"]}' for n, t in trafos_index_in_service.iterrows()])

        # вывод трансформаторов выведенных из работы
        trafos_index_not_in_service = net.trafo.loc[net.trafo['in_service'] == False]
        collections_data['trafos'].extend(trafos_index_not_in_service.index.tolist())
        if len(trafos_index_not_in_service):
            tr_not_in_service = plot.create_trafo_collection(net, trafos=trafos_index_not_in_service.index, size=0.05,
                                                             linewidths=0.4, linestyle='--', bus_geodata=bus_geodata)
            collections_data['collections'].append(tr_not_in_service)
            circles = tr_not_in_service[0].get_paths()
            collections_data['coords_trafos'].extend([(coord.vertices[0][0], coord.vertices[0][1] + 0.06) for coord in
                                                      circles[::2]])

            trafos_name.extend([f'{t.at["name"]}' for n, t in trafos_index_not_in_service.iterrows()])

            trafos_mark.extend([f'{t.at["std_type"]}' for n, t in trafos_index_not_in_service.iterrows()])

        if trafos_mark:
            collections_data['collections'].append(create_annotation_shift(trafos_mark, collections_data['coords_trafos'],
                                                                           0.03, 3 * text_size, text_size))
        if trafos_name:
            collections_data['collections'].append(create_annotation_shift(trafos_name, collections_data['coords_trafos'],
                                                                           0.03, 4 * text_size, text_size))

        trafos3w_name =[]
        trafos3w_mark = []
        # вывод трёхобмоточных трансформаторов в работе
        trafos_index_in_service = net.trafo3w.loc[net.trafo3w['in_service']]
        collections_data['trafos3w'] = trafos_index_in_service.index.tolist()
        if len(trafos_index_in_service):
            tr3w_in_service = create_trafo3w_collection(net, trafo3ws=trafos_index_in_service.index, size=0.05)

            collections_data['collections'].append(tr3w_in_service)

            circles = tr3w_in_service[0].get_paths()
            collections_data['coords_trafos3w'].extend([(coord.vertices[0][0], coord.vertices[0][1] + 0.06) for coord in
                                                        circles[::3]])

            trafos3w_name.extend([f'{t.at["name"]}' for n, t in trafos_index_in_service.iterrows()])
            trafos3w_mark.extend([f'{t.at["std_type"]}' for n, t in trafos_index_in_service.iterrows()])

        # вывод трёхобмоточных трансформаторов выведенных из работы
        trafos_index_not_in_service = net.trafo3w.loc[net.trafo3w['in_service'] == False]
        collections_data['trafos3w'].extend(trafos_index_not_in_service.index.tolist())
        if len(trafos_index_not_in_service):
            tr3w_not_in_service = create_trafo3w_collection(net, trafo3ws=trafos_index_not_in_service.index, size=0.05, linestyle='--')

            collections_data['collections'].append(tr3w_not_in_service)

            circles = tr3w_not_in_service[0].get_paths()
            collections_data['coords_trafos3w'].extend([(coord.vertices[0][0], coord.vertices[0][1] + 0.06) for coord in
                                                        circles[::3]])

            trafos3w_name.extend([f'{t.at["name"]}' for n, t in trafos_index_not_in_service.iterrows()])
            trafos3w_mark.extend([f'{t.at["std_type"]}' for n, t in trafos_index_not_in_service.iterrows()])

        collections_data['collections'].append(create_annotation_shift(trafos3w_name, collections_data['coords_trafos3w'],
                                                                       0.03, -2*text_size, text_size))

        collections_data['collections'].append(create_annotation_shift(trafos3w_mark, collections_data['coords_trafos3w'],
                                                                       0.03, -3*text_size, text_size))


    # вывод сборных шин
    # bbc = plot.create_busbar_collection(net, buses=[0,1,2,3,4,5,6,7,8], color='k', linewidth=3)
    # collections_data['collections'].append(bbc)


    # вывод линий
    lines_not_in_service = set([line for line in net.line.index.tolist() if net.line.in_service.loc[line] == False])
    lines_with_geo = set(net.line_geodata.index.tolist()) - lines_not_in_service
    lines_without_geo = list(set(net.line.index.tolist()) - lines_not_in_service - lines_with_geo)
    lines_with_geo = list(lines_with_geo)
    collections_data['lines'] = lines_without_geo + lines_with_geo

    lc = plot.create_line_collection(net, color='k', lines=lines_without_geo, linewidths=0.3, use_bus_geodata=True)
    lc_with_geo = plot.create_line_collection(net, lines=lines_with_geo, color='k', linewidths=0.3,
                                              use_bus_geodata=False)
    paths_lines = lc.get_paths() if lc else []
    paths_lines.extend(lc_with_geo.get_paths() if lc_with_geo else [])


    collections_data['coords_lines'] = [(line.vertices[0][0], line.vertices[0][1], line.vertices[1][0],
                                         line.vertices[1][1]) for line in paths_lines]
    # вывод марки кабеля/провода
    line_names = []
    for line in collections_data['lines']:
        text = '  '
        if index:
            text += f'({line}) '
        text += f'{net.line.loc[line].std_type}'
        line_names.append(text)
    coords = calc_coords_annotation(collections_data['coords_lines'], 0, text_size)
    collections_data['collections'].append(create_annotation(size=text_size, texts=line_names,
                                                             coords=coords))
    # вывод длины кабеля/провода
    line_names = []
    for line in collections_data['lines']:
        text = f'{net.line.loc[line].length_km}км'
        line_names.append(text)
    coords = calc_coords_annotation(collections_data['coords_lines'], 1, text_size)
    collections_data['collections'].append(create_annotation(size=text_size, texts=line_names,
                                                             coords=coords))

    # вывод секционных выключателей
    switches, helper_lines = plot.create_bus_bus_switch_collection(net, size=0.1, helper_line_size=2,
                                                                   helper_line_color='k',
                                                                   helper_line_style='-')
    helper_lines.set_zorder(0)
    helper_lines.set_linewidth(1)
    collections_data['collections'].extend([lc, lc_with_geo, (switches, helper_lines)])

    # вывод выключателей
    switches = plot.create_line_switch_collection(net, size=0.1, distance_to_bus=0.5, use_line_geodata=True)
    switches.set_zorder(2)
    collections_data['collections'].append(switches)

    return collections_data

def plot_net_pf(net, collections_data, text_size: float = 0.05):
    # вывод токов
    line_names = [f'Iбтн(н)={net.res_line.loc[line, "i_from_ka"]*1000: .1f}A'.strip() for line in collections_data['lines']]
    collections_data['collections'].append(create_annotation(size=text_size,
                                                             texts=line_names,
                                                             coords=calc_coords_annotation(collections_data['coords_lines'], 2, text_size)))
    # вывод токов
    line_names = [
        f'Iбтн(к)={net.res_line.loc[line, "i_to_ka"] * 1000: .1f}A'.strip()
        for line in collections_data['lines']]
    collections_data['collections'].append(create_annotation(size=text_size,
                                                             texts=line_names,
                                                             coords=calc_coords_annotation(
                                                                 collections_data['coords_lines'], 3, text_size)))

def plot_net_ic(net, collections_data, text_size: float = 0.05):
    # вывод удельных ёмкостей
    line_names = [f'{net.std_types["line"][net.line.loc[line].std_type]["c_nf_per_km"]: .1f}нФд/км'.strip()
                  for line in collections_data['lines']]
    collections_data['collections'].append(create_annotation(size=text_size,
                                    texts=line_names,
                                    coords=calc_coords_annotation(collections_data['coords_lines'], 2, text_size)))

    # вывод ёмкостей
    line_names = [
        f'{net.std_types["line"][net.line.loc[line].std_type]["c_nf_per_km"] * net.line.loc[line].length_km: .1f}нФд'.strip()
        for line in collections_data['lines']]
    collections_data['collections'].append(create_annotation(size=text_size,
                                    texts=line_names,
                                    coords=calc_coords_annotation(collections_data['coords_lines'], 3, text_size)))

    # вывод ёмкостных токов
    line_names = [f'Ic={net.res_line.loc[line, "i_from_ka"]*3000: .3f}A'.strip() for line in collections_data['lines']]
    collections_data['collections'].append(create_annotation(size=text_size,
                                    texts=line_names,
                                    coords=calc_coords_annotation(collections_data['coords_lines'], -1, text_size)))

    # вывод ёмкостных токов
    line_names = [
        f'Ic(к)={net.res_line.loc[line, "i_to_ka"] * 3000: .1f}A'.strip()
        for line in collections_data['lines']]
    collections_data['collections'].append(create_annotation(size=text_size,
                                                             texts=line_names,
                                                             coords=calc_coords_annotation(
                                                                 collections_data['coords_lines'], -2, text_size)))
    # вывод места замыкания
    sx = -1.5
    sy = -0.5
    segs = np.zeros((1, 7, 2))
    x = np.array([0.03, 0, 0,    0, 0.1, 0.04, 0.1]) + sx
    y = np.array([0,    0, 0.03, 0, 0.15, 0.12, 0.21]) +sy
    segs[0, :, 0] = x
    segs[0, :, 1] = y
    collections_data['collections'].append(LineCollection(segs, linewidths=0.7))
    collections_data['collections'].append(create_annotation(size=text_size, texts=['K(1)'], coords=[(sx-0.1, sy+0.15)]))

def draw(collection, name_file):
    plot.draw_collections(collection)
    savefig(f'{name_file}.png', format="png", dpi=1500)