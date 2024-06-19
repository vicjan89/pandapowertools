import os
import json
import tomllib
import math


import pandapower as pp


from pandapowertools.functions import russian_to_attribute_name


class Attrs:
    ...

class Net:

    def __init__(self, name: str, path: str = ''):
        self.name = name
        self.path = path
        self.modes = {}
        self.net = pp.create_empty_network(name)
        self.b = Attrs()
        self.l = Attrs()
        self.t = Attrs()
        self.t3 = Attrs()
        self.s = Attrs()
        self._update_std()
        self.et = Attrs()
        self.et.line = 'l'
        self.et.trafo = 't'
        self.et.trafo3w = 't3'
        self.et.bus = 'b'

    def add_std(self):
        current_path = os.path.realpath(__file__)
        current_path = os.path.dirname(current_path)
        with open(os.path.join(current_path, 'std_lines.toml'), 'rb') as f:
            data = tomllib.load(f)
        pp.create_std_types(self.net, data, element='line', overwrite=True, check_required=True)
        with open(os.path.join(current_path, 'std_trafos.toml'), 'rb') as f:
            data = tomllib.load(f)
        pp.create_std_types(self.net, data, element='trafo', overwrite=True, check_required=True)
        with open(os.path.join(current_path, 'std_trafos3w.toml'), 'rb') as f:
            data = tomllib.load(f)
        pp.create_std_types(self.net, data, element='trafo3w', overwrite=True, check_required=True)
        self._update_std()


    def _update_std(self):
        attrs = {}
        for key, value in self.net.std_types.items():
            for name_std in value:
                if key == 'trafo3w':
                    prefix = 't3_'
                else:
                    prefix = key[0] + '_'
                attrs[f'{prefix}{russian_to_attribute_name(name_std)}'] = name_std
        self.std = Attrs()
        self.std.__dict__.update(attrs)

    def _line_to_attr(self, index):
        from_bus = self.net.line.at[index, 'from_bus']
        to_bus = self.net.line.at[index, 'to_bus']
        name = f'{self.net.bus.at[from_bus, "name"]}_{self.net.bus.at[to_bus, "name"]}'
        return 'l' + russian_to_attribute_name(name)

    def add_line(self, from_bus: int, to_bus: int, length: float, std_type: str, parallel: int = 1):
        index = pp.create_line(self.net, from_bus, to_bus, length, std_type, parallel=parallel)
        self.net.line["endtemp_degree"] = 20
        self.l.__dict__.update({self._line_to_attr(index): index})

    def _switch_to_attr(self, index):
        item = self.net.switch.loc[index]
        name1 = ''
        try:
            name1 = self.net.bus.at[item['bus'], 'name']
        except KeyError:
            ...
        name2 = ''
        try:
            if item['et'] == 't':
                name2 = self.net.trafo.at[item['element'], 'name']
            if item['et'] == 'l':
                name2 = '_line_' + self.names_line[item['element']]
        except KeyError:
            ...
        name = name1 + ' - ' + name2
        return 's' + russian_to_attribute_name(name)

    def add_switch(self, bus, element, et, closed=True):
        index = pp.create_switch(self.net, bus, element, et, closed)
        self.switch.__dict__.update({self._switch_to_attr(index): index})

    def add_bus(self, un: float, name: str = ''):
        index = pp.create_bus(self.net, un, name)
        self.b.__dict__.update({'b' + russian_to_attribute_name(name): index})

    def _trafo_to_attr(self, index):
        name = f'{self.net.trafo.at[index, "name"]}'
        return 't' + russian_to_attribute_name(name)

    def add_trafo(self, hv_bus, lv_bus, std_type, name):
        index = pp.create_transformer(self.net, hv_bus, lv_bus, std_type, name)
        self.trafo.__dict__.update({self._trafo_to_attr(index): index})

    def _trafo3w_to_attr(self, index):
        name = f'{self.net.trafo3w.at[index, "name"]}'
        return 't' + russian_to_attribute_name(name)

    def add_trafo3w(self, hv_bus, mv_bus, lv_bus, std_type, name):
        index = pp.create_transformer3w(self.net, hv_bus, mv_bus, lv_bus, std_type, name)
        self.t3.__dict__.update({self._trafo3w_to_attr(index): index})

    def add_impedance(self, from_bus, to_bus, r, x, s):
        index = pp.create_impedance(self.net, from_bus, to_bus, r, x, s)

    def add_ext_grid(self, bus, ikz_max: float, ikz_min: float | None = None):
        '''
        Create extension grid
        :param bus: bus where the slack is connected
        :param ikz_max: ikz in maximum mode in kiloampere
        :param ikz_min: ikz in minimum mode in kiloampere
        :return:
        '''
        if not ikz_min:
            ikz_min = ikz_max
        u_bus = self.net.bus.at[bus, 'vn_kv']
        item = {}
        item['s_sc_max_mva'] = u_bus * ikz_max * math.sqrt(3)
        item['s_sc_min_mva'] = u_bus * ikz_min * math.sqrt(3)
        item['rx_max'] = 0.1
        item['rx_min'] = 0.1
        item['bus'] = bus
        pp.create_ext_grid(net=self.net, **item)

    def add_load(self, bus, p_mw, q_mvar: float = 0):
        pp.create_load(self.net, bus, p_mw, q_mvar)

    def save(self):
        file = f'{self.name}.json'
        if self.path:
            path = os.path.join(self.path, file)
        else:
            path = file
        pp.to_json(self.net, path)
        if self.modes:
            file = f'{self.name}_modes.json'
            if self.path:
                path = os.path.join(self.path, file)
            else:
                path = file
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.modes, f, ensure_ascii=False, indent=4)

    def load(self):
        file = f'{self.name}.json'
        if self.path:
            path = os.path.join(self.path, file)
        else:
            path = file
        self.net = pp.from_json(path)
        attrs = {}
        for i, b in self.net.bus.iterrows():
            attrs['b' + russian_to_attribute_name(b['name'])] = i
        self.b.__dict__.update(attrs)
        attrs = {}
        for i in self.net.line.index.to_list():
            attrs[self._line_to_attr(i)] = i
        self.l.__dict__.update(attrs)
        attrs = {}
        for i in self.net.trafo.index.to_list():
            attrs[self._trafo_to_attr(i)] = i
        self.t.__dict__.update(attrs)
        attrs = {}
        for i in self.net.trafo3w.index.to_list():
            attrs[self._trafo3w_to_attr(i)] = i
        self.t3.__dict__.update(attrs)
        attrs = {}
        for i in self.net.switch.index.to_list():
            attrs[self._switch_to_attr(i)] = i
        self.s.__dict__.update(attrs)
        attrs = {}
        for key, value in self.net.std_types.items():
            for name_std in value:
                if key == 'trafo3w':
                    prefix = 't3_'
                else:
                    prefix = key[0] + '_'
                attrs[f'{prefix}{russian_to_attribute_name(name_std)}'] = name_std
        self.std.__dict__.update(attrs)

        try:
            file = f'{self.name}_modes.json'
            if self.path:
                path = os.path.join(self.path, file)
            else:
                path = file
            with open(path, 'r', encoding='utf-8') as f:
                self.modes = json.load(f)
        except FileNotFoundError:
            print('File of modes not exist!')

    def scheme(self):
        print('bus')
        for i, row in self.net.bus.iterrows():
            name_bus = row['name'].ljust(20)
            istr = str(i).rjust(4)
            try:
                x = self.net.bus_geodata.loc[i, 'x']
                y = self.net.bus_geodata.loc[i, 'y']
            except:
                x = 'No'
                y = 'No'
            print(f'{istr}) {name_bus} {str(row["vn_kv"]).ljust(7)} x={x} y={y}')
        print('ext_grid')
        for i, row in self.net.ext_grid.iterrows():
            name_bus = self.net.bus.loc[row['bus'], 'name'].ljust(28)
            print(f'{name_bus} s_sc_max_mva={row["s_sc_max_mva"]} s_sc_min_mva={row["s_sc_min_mva"]}')
        print('line')
        for i, row in self.net.line.iterrows():
            name_from = self.net.bus.loc[row['from_bus'], 'name'].ljust(18)
            name_to = self.net.bus.loc[row['to_bus'], 'name'].rjust(18)
            l = row['length_km']
            r = row['r_ohm_per_km'] * l
            x = row['x_ohm_per_km'] * l
            z = math.sqrt(r**2 + x**2)
            std_type = row['std_type'].ljust(18)
            istr = str(i).rjust(3)
            l = str(l).rjust(7)
            print(f'{istr}) {name_from} {name_to} {row["parallel"]:.0f}*{std_type} {l} {r:.4f}+j{x:.4f}={z:.4f}')
        print('trafo')
        for i, row in self.net.trafo.iterrows():
            name_hv = self.net.bus.loc[row['hv_bus'], 'name'].ljust(28)
            name_lv = self.net.bus.loc[row['lv_bus'], 'name'].rjust(28)
            print(f'{name_hv} {name_lv} {row["name"]} {row["std_type"]}')
        print('trafo3w')
        for i, row in self.net.trafo3w.iterrows():
            name_hv = self.net.bus.loc[row['hv_bus'], 'name'].ljust(28)
            name_mv = self.net.bus.loc[row['mv_bus'], 'name'].ljust(28)
            name_lv = self.net.bus.loc[row['lv_bus'], 'name'].rjust(28)
            print(f'{name_hv} {name_mv} {name_lv} {row["name"]} {row["std_type"]}')
        print('impedance')
        for i, row in self.net.impedance.iterrows():
            name_from = self.net.bus.loc[row['from_bus'], 'name'].ljust(28)
            name_to = self.net.bus.loc[row['to_bus'], 'name'].rjust(28)
            u2 = self.net.bus.loc[row['from_bus'], 'vn_kv'] ** 2
            zb = u2 / row['sn_mva']
            rpu = row['rtf_pu']
            xpu = row['xtf_pu']
            print(f'{name_from} {name_to} rft_pu={rpu} xft_pu={xpu} r={rpu*zb} x={xpu*zb}')
        print('switch')
        names = self.names_switch
        for i, row in self.net.switch.iterrows():
            print(f'{names[i]} {"closed" if row["closed"] else "opened"}')

    def bus_geodata(self):
        for i, geodata in self.net.bus_geodata.sort_index().iterrows():
            name = self.net.bus.loc[i, 'name'].ljust(20)
            istr = str(i).rjust(4)
            print(f'{istr}) {name} x={geodata["x"]} y={geodata["y"]}')

    def busxy(self, i, x, y):
        self.net.bus_geodata.loc[i, 'x'] = x
        self.net.bus_geodata.loc[i, 'y'] = y

    def add_mode(self, name: str, closed: tuple = tuple(), opened: tuple = tuple()):
        self.modes[name] = {'closed': closed, 'opened': opened}

    def make_mode(self, mode_name):
        if mode_name in self.modes:
            self.net.switch.loc[self.modes[mode_name]['closed'], 'closed'] = True
            self.net.switch.loc[self.modes[mode_name]['opened'], 'closed'] = False
        else:
            print('Mode not specified')

    def calc_pf_mode(self, mode_name):
        tolerance = 1e-8
        self.make_mode(mode_name)
        for i in range(15):
            try:
                pp.runpp(self.net, tolerance_mva=tolerance, switch_rx_ratio=1)
                print(f'PowerFlow calculated witn tolerance {tolerance}')
                break
            except pp.powerflow.LoadflowNotConverged:
                tolerance *= 10
        else:
            print(f'PowerFlow not calculated with tolerance {tolerance}')

    def create_mode_magnetizing_current_inrush(self, k: float=4):
        self.net.load['in_service'] = False
        index_magnetizing_current_inrush = []
        for i, tr in self.net.trafo.iterrows():
            index_magnetizing_current_inrush.append(pp.create_load(self.net, tr.hv_bus, p_mw=tr.sn_mva * k))
        for i, tr in self.net.trafo3w.iterrows():
            index_magnetizing_current_inrush.append(pp.create_load(self.net, tr.hv_bus, p_mw=tr.sn_hv_mva * k))
        return index_magnetizing_current_inrush

    def delete_mode_magnetizing_current_inrush(self, index_magnetizing_current_inrush: list):
        pp.toolbox.drop_elements(self.net, element_type='load', element_index=index_magnetizing_current_inrush)
        for i, l in self.net.load.iterrows():
            l.in_service = True

    def calc_sc_mode(self, mode_name: str, fault: str='3ph', case: str='max'):
        self.make_mode(mode_name)
        pp.shortcircuit.calc_sc(self.net, fault=fault, case=case, branch_results=True, return_all_currents=True)

    def calc_sc(self, fault: str='3ph', case: str='max'):
        pp.shortcircuit.calc_sc(self.net, fault=fault, case=case)

    def res_bus_sc(self):
        s = 'Точка КЗ | Ток КЗ, кА | r, Ом | x, Ом | z, Ом\n-|-|-|-|-\n'
        res = self.net.res_bus_sc
        for index, row in res.sort_index().iterrows():
            name = self.net.bus.loc[index, 'name'].ljust(28)
            i = f'{row.loc["ikss_ka"]:.2f}'.ljust(7)
            r = row.loc["rk_ohm"]
            rstr = f'{r:.6f}'.ljust(10)
            x = row.loc["xk_ohm"]
            xstr = f'{x:.6f}'.ljust(10)
            s += f'{name} | {i} | {rstr} | {xstr} | {math.sqrt(r**2 + x**2):.6f}\n'
        return s

    @property
    def names_line(self):
        names = []
        for _, item in self.net.line.iterrows():
            try:
                name1 = self.net.bus.at[item['from_bus'], 'name']
            except KeyError:
                ...
            if not name1:
                name1 = ''
            try:
                name2 = self.net.bus.at[item['to_bus'], 'name']
            except KeyError:
                ...
            if not name2:
                name2 = ''
            name = name1 + ' - ' + name2
            names.append(name)
        return names

    @property
    def names_trafo(self):
        return self.net.trafo['name'].tolist()

    @property
    def names_trafo3w(self):
        return self.net.trafo3w['name'].tolist()

    @property
    def names_switch(self):
        names = []
        names_line = self.names_line
        for _, item in self.net.switch.iterrows():
            name1 = ''
            try:
                name1 = self.net.bus.at[item['bus'], 'name']
            except KeyError:
                ...
            name2 = ''
            try:
                if item['et'] == 't':
                    name2 = self.net.trafo.at[item['element'], 'name']
                if item['et'] == 'l':
                    name2 = names_line[item['element']]
            except KeyError:
                ...
            name = name1 + ' - ' + name2
            names.append(name)
        return names

    @property
    def names_bus(self):
        return self.net.bus['name'].to_list()

    def place_buses(self, buses: int | list | tuple, bus_to: int | None=None, x=0, y=0, step=2):
        if isinstance(buses, int):
            buses = [buses]
        if bus_to is not None:
            x = self.net.bus_geodata.loc[bus_to, 'x'] + x
            y = self.net.bus_geodata.loc[bus_to, 'y'] + y
        for bus in buses:
            self.net.bus_geodata.loc[bus, 'x'] = x
            self.net.bus_geodata.loc[bus, 'y'] = y
            x += step

    def move_bus(self, bus, bus_to, dx: float | None = None, dy: float | None = None):
        if dx is not None:
            self.net.bus_geodata.loc[bus, 'x'] = self.net.bus_geodata.loc[bus_to, 'x'] + dx
        if dy is not None:
            self.net.bus_geodata.loc[bus, 'y'] = self.net.bus_geodata.loc[bus_to, 'y'] + dy

    def shift_buses(self, buses, bus_to: int | None=None, dx=0, dy=0):
        '''
        Shift coords of buses. If define bus_to then shift is doing from coords bus_to and buses[0]
        :param buses:
        :param bus_to:
        :param dx:
        :param dy:
        :return:
        '''
        if isinstance(buses, int):
            buses = [buses]
        if bus_to is not None:
            dx = self.net.bus_geodata.loc[bus_to, 'x'] - self.net.bus_geodata.loc[buses[0], 'x'] + dx
            dy = self.net.bus_geodata.loc[bus_to, 'y'] - self.net.bus_geodata.loc[buses[0], 'y'] + dy
        for bus in buses:
            self.net.bus_geodata.loc[bus, 'x'] += dx
            self.net.bus_geodata.loc[bus, 'y'] += dy

    def select_rect(self, x1, y1, x2, y2):
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        buses = []
        for i, bus_geodata in self.net.bus_geodata.iterrows():
            if x1 <= bus_geodata['x'] <= x2 and y1 <= bus_geodata['y'] <= y2:
                buses.append(i)
        return buses


    def coord_buses(self, buses, x: float | None = None, y: float | None = None):
        if isinstance(buses, int):
            buses = [buses]
        for bus in buses:
            if x is not None:
                self.net.bus_geodata.loc[bus, 'x'] = x
            if y is not None:
                self.net.bus_geodata.loc[bus, 'y'] = y
